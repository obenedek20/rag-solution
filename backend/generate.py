"""
Functions for retrieval and generation for RAG system (online portion of pipeline)
"""

import faiss
import numpy as np
import json
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from company_lookup import route, build_entity_map, ask_llm
import os
from sentence_transformers import CrossEncoder
from collections import defaultdict

###############################
# Querying (Online)
###############################
# Use same embedding model as indexing step to ensure embeddings are in same vector space
embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    device="mps" # more efficient when using Apple Silicon
)

RERANKER = CrossEncoder("BAAI/bge-reranker-base")

# Query embedding
def embed_query(q: str):
    return embed_model._model.encode(
        [q],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")

# gets company indexes from registry.json and loads faiss index and nodes for each company
def retrieve_company_indexes():
    BASE_DIR = "storage"

    with open(os.path.join(BASE_DIR, "registry.json"), "r") as f:
        registry = json.load(f)

    companies = registry["companies"]

    company_indexes = {}

    for company in companies:
        company_dir = os.path.join(BASE_DIR, company)

        # Load FAISS index
        index_path = os.path.join(company_dir, "index.faiss")
        index = faiss.read_index(index_path)

        # Load nodes
        with open(os.path.join(company_dir, "nodes.json"), "r") as f:
            nodes = json.load(f)

        company_indexes[company] = {
            "index": index,
            "nodes": nodes  # list of dicts (text + metadata)
        }
    return company_indexes

# retrieves relevant nodes based on query and whether we use global or per-company retrieval
# gets 10 per ticker or 40 for global (before reranking)
def retrieve(query, ENTITY_MAP):

    route_info = route(query, ENTITY_MAP)

    vec = embed_query(query)

    results = []

    mode = route_info["mode"] # global or entity

    # CASE 1: GLOBAL
    if mode == "global":
        with open("nodes.json", "r") as f:
            all_nodes = json.load(f)
        global_index = faiss.read_index("global.index.faiss") # binary vector db with embeddings of size n
        scores, idx = global_index.search(vec, k=40)
        results = [all_nodes[i] for i in idx[0]]

    # CASE 2: PER-COMPANY (entity)
    else:
        company_indexes = retrieve_company_indexes()
        for ticker in route_info["tickers"]:
            index = company_indexes[ticker]["index"]
            nodes = company_indexes[ticker]["nodes"]

            scores, idx = index.search(vec, k=10)

            results.extend(nodes[i] for i in idx[0])

    return rerank(results, query, mode)

# reranks pulled nodes based on query using a cross-encoder model
# if global, return top 8, else return top 4 per company
def rerank(results, query, mode):
    pairs = [
        (query, node["text"])
        for node in results
    ]

    rerank_scores = RERANKER.predict(pairs)

    ranked = sorted(
        zip(rerank_scores, results),
        key=lambda x: x[0],
        reverse=True
    )

    # ---------- GLOBAL SEARCH ----------
    if mode == "global":
        return [node for _, node in ranked[:8]]

    # ---------- PER-COMPANY SEARCH ----------
    else:
        per_company = 4

        company_counts = defaultdict(int)
        selected = []

        for score, node in ranked:
            ticker = node["metadata"]["company"]

            if company_counts[ticker] >= per_company:
                continue

            selected.append(node)
            company_counts[ticker] += 1

        return selected

# Build final LLM prompt
def build_prompt(query, results):
    context = ""

    for i, result in enumerate(results, start=1):
        filename = result["metadata"].get("file_name", "Unknown")

        context += f"""
    [Source {i}: {filename}]

    {result["text"]}

    """

    return f"""
You are a financial research assistant that answers questions
using only SEC EDGAR filing excerpts provided to you. You do not give investment
advice or recommendations — only factual information grounded in the filings. 

Rules:
1. Use ONLY the provided context. Do not use prior knowledge about these companies.
2. Every factual claim must be attributed to a specific source chunk's file name, e.g. [AAPL_10K_2024Q3_2024-11-01_full.txt].
3. If chunks come from different companies or fiscal periods, never blend their data 
   together unless the question explicitly asks for a comparison — and if you do 
   compare, label each figure with its company and period.
4. Preserve numbers, units, and currency exactly as written (e.g., "$1.2M" vs 
   "$1,200,000" — don't convert or recompute unless asked).
5. If the context only partially answers the question, answer the part you can and 
   explicitly state what's missing.
6. If the context doesn't address the question at all, say so plainly — don't guess.
7. Never invent a source number that wasn't given to you.

Context:
{context}

Question:
{query}
"""

# main function to process query: retrieves relevant nodes, builds prompt, and sends to LLM
def process_query(prompt, ENTITY_MAP):
    print(f"Query: {prompt}")
    print(f"Retrieving relevant nodes...")
    results = retrieve(prompt, ENTITY_MAP)
    print(f"Retrieved {len(results)} nodes.")
    rag_prompt = build_prompt(prompt, results)
    print("Sending prompt to LLM...")
    print("Prompt: " + rag_prompt)
    response = ask_llm(rag_prompt)
    print("Response: " + response)
    return response
