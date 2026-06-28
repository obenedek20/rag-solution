"""
Functions for indexing (per-company and global) for RAG system (offline portion of pipeline)
"""

from ollama import chat
from llama_index.core import SimpleDirectoryReader
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser, SentenceSplitter
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import re
import os
import argparse
from company_lookup import retrieve_companies_from_tickers

def normalize(text):
    text = text.lower()

    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"\d+", "<num>", text)

    return text.strip()

###############################
# Indexing (Offline)
###############################
# load data from edgar_corpus
def load_documents():
    print("Loading documents from edgar_corpus...")
    documents = SimpleDirectoryReader("edgar_corpus").load_data()
    print(f"Loaded {len(documents)} documents")

    for doc in documents:
        file_name = doc.metadata.get("file_name", "")
        doc.metadata["company"] = file_name.split("_")[0]

    total_chars = sum(len(doc.text) for doc in documents)
    total_words = sum(len(doc.text.split()) for doc in documents)

    print(f"Documents: {len(documents)}")
    print(f"Characters: {total_chars:,}")
    print(f"Words: {total_words:,}")
    return documents

def create_nodes(documents):
    # Create embedding model
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        device="mps" # more efficient when using Apple Silicon
    )

    print("Creating sentence splitter node parser...")
    splitter = SentenceSplitter( # since edgar filings have clear structure, sometimes better (and faster) to use chunks instead of semantic spliting
        chunk_size=256,
        chunk_overlap=32,
        include_metadata=True
    )

    print("Getting nodes from documents...")
    nodes = splitter.get_nodes_from_documents(
        documents,
        show_progress=True
    )
    return nodes, embed_model

###############################
# Pre-processing / Filtering
###############################
def filter_nodes(nodes):
    SKIP_PHRASES = [
        # --- SEC cover / filing header boilerplate ---
        "commission file number",
        "securities and exchange commission",
        "washington, d.c. 20549",
        "united states securities and exchange commission",
        "check the appropriate box",
        "emerging growth company",
        "large accelerated filer",
        "accelerated filer",
        "non-accelerated filer",
        "smaller reporting company",
        "not applicable",
        "no filing fee required",

        # --- Identity / registration metadata (low value for RAG) ---
        "exact name of registrant",
        "state or other jurisdiction of incorporation",
        "irs employer identification number",
        "principal executive offices",
        "telephone number",
        "securities registered pursuant to section",
        "trading symbol",
        "name of each exchange",

        # --- Navigation / structure noise ---
        "table of contents",
        "index to exhibits",
        "exhibit index",
        "table of exhibits",
        "list of exhibits",

        # --- Signature / certification boilerplate ---
        "signatures",
        "pursuant to the requirements of",
        "the registrant has duly caused",
        "to be signed on its behalf",
        "authorized officer",
        "power of attorney",

        # --- XBRL / machine-readable metadata noise ---
        "inline xbrl",
        "xbrl instance document",
        "taxonomy extension",
        "calculation linkbase",
        "presentation linkbase",
        "definition linkbase",
        "label linkbase",
        "reference linkbase",
        "schema document",

        # --- Filing metadata artifacts ---
        "accession number",
        "central index key",
        "filed pursuant to",
        "sec file number",
        "document type",

        # --- Page artifacts ---
        "this page intentionally left blank",

        # --- Form identifiers (often noisy headers/footers) ---
        "form 10-k",
        "form 10-q",
        "form 8-k",
        "annual report pursuant to section",
        "quarterly report pursuant to section",
    ]
    # Removing duplicate or near duplicate nodes - numbers and whitespace are normalized to reduce false negatives
    seen = set()
    filtered = []

    skipped_nodes = 0

    for node in nodes:
        text = node.text.lower()

        if any(p in text for p in SKIP_PHRASES):
            skipped_nodes += 1
            continue

        key = normalize(node.text)

        if key in seen:
            skipped_nodes += 1
            continue

        seen.add(key)
        filtered.append(node)

    nodes = filtered

    print(f"Filtered nodes: {len(nodes)} (skipped {skipped_nodes})")
    return nodes

def per_company_indexing_setup(nodes, embed_model):
    company_nodes = {}
    for node in nodes:
        company = node.metadata["company"]
        company_nodes.setdefault(company, []).append(node)
    # Now we have AAPL → [nodes...] MSFT → [nodes...] NVDA → [nodes...]

    # each node has node.text, node.metadata
    texts = [node.text for node in nodes]
    metadatas = [node.metadata for node in nodes]

    model = embed_model._model
    # Per company embeddings dictionary
    print("Encoding texts into embeddings for per-company embeddings...")
    company_embeddings = {}
    for company, c_nodes in company_nodes.items():
        texts = [n.text for n in c_nodes]

        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        company_embeddings[company] = (c_nodes, embeddings)

    print("Creating FAISS indexes for per-company embeddings...")
    company_indexes = {}
    dim = None

    for company, (nodes_list, embeddings) in company_embeddings.items():

        if dim is None:
            dim = embeddings.shape[1]

        index = faiss.IndexFlatIP(dim)
        index.add(embeddings.astype(np.float32))

        company_indexes[company] = {
            "index": index,
            "nodes": nodes_list
        }
    return company_indexes, company_embeddings
    # Now have AAPL → FAISS + nodes, MSFT → FAISS + nodes, NVDA → FAISS + nodes

def global_indexing_setup(company_embeddings):
    # Now create global embeddings and FAISS index
    all_nodes = []
    all_embeddings = []

    for company, (nodes_list, embs) in company_embeddings.items():
        all_nodes.extend(nodes_list)
        all_embeddings.append(embs)

    all_embeddings = np.vstack(all_embeddings)

    global_index = faiss.IndexFlatIP(dim)
    global_index.add(all_embeddings.astype(np.float32))

    return global_index, all_nodes

def save_indexes(company_indexes, global_index, all_nodes):
    BASE_DIR = "storage"
    os.makedirs(BASE_DIR, exist_ok=True)
    for company, data in company_indexes.items():

        company_dir = os.path.join(BASE_DIR, company)
        os.makedirs(company_dir, exist_ok=True)

        # 1. Save FAISS index
        print(f"Saving FAISS index for {company}")
        faiss.write_index(
            data["index"],
            os.path.join(company_dir, "index.faiss")
        )
        
        nodes = data["nodes"]
        print(f"Saving nodes for {company} ({len(nodes)} nodes)")
        with open(os.path.join(company_dir, "nodes.json"), "w") as f:
            json.dump(
                [
                    {
                        "text": n.text,
                        "metadata": n.metadata
                    }
                    for n in nodes
                ],
                f,
                indent=2
            )

    registry = {
        "companies": list(company_indexes.keys())
    }

    with open(os.path.join(BASE_DIR, "registry.json"), "w") as f:
        json.dump(registry, f, indent=2)

    faiss.write_index(global_index, "global.index.faiss") # binary file created - can now be referenced
    print(f"Saved FAISS index with {global_index.ntotal} vectors to global.index.faiss")
    with open("nodes.json", "w") as f: # create node file that stores text, metadata
        json.dump(
            [
                {
                    "id": i,
                    "text": node.text,
                    "metadata": node.metadata
                }
                for i, node in enumerate(all_nodes)
            ],
            f,
            indent=2
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--no-indexing",
        "-i",
        action="store_true",
        help="Build indexes"
    )

    parser.add_argument(
        "--no-company-map",
        "-c",
        action="store_true",
        help="Generate companies.json"
    )

    args = parser.parse_args()

    if (not args.no_indexing):
        ## Create indexes - necessary pre-processing
        documents = load_documents()
        nodes, embed_model = create_nodes(documents)
        nodes = filter_nodes(nodes)
        company_indexes, company_embeddings = per_company_indexing_setup(nodes, embed_model)
        global_index, all_nodes = global_indexing_setup(company_embeddings)
        save_indexes(company_indexes, global_index, all_nodes)

    ## Generate companies.json for entity mapping
    if (not args.no_company_map):
        retrieve_companies_from_tickers() # creates companies.json