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

###############################
# Querying (Online)
###############################
embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    device="mps" # more efficient when using Apple Silicon
)

# chunks sent to LLM are the nodes from the json file - faiss index is used to pick nodes (ids in faiss match up to node json)

# Query embedding
def embed_query(q: str):
    return embed_model._model.encode(
        [q],
        convert_to_numpy=True,
        normalize_embeddings=True
    ).astype("float32")


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

def retrieve(query, ENTITY_MAP):

    route_info = route(query, ENTITY_MAP)

    vec = embed_query(query)

    results = []

    # CASE 1: GLOBAL
    if route_info["mode"] == "global":
        with open("nodes.json", "r") as f:
            all_nodes = json.load(f)
        global_index = faiss.read_index("global.index.faiss") # binary vector db with embeddings of size n
        scores, idx = global_index.search(vec, k=40)
        results = [all_nodes[i] for i in idx[0]]

    # CASE 2: PER-COMPANY
    else:
        company_indexes = retrieve_company_indexes()
        for ticker in route_info["tickers"]:
            index = company_indexes[ticker]["index"]
            nodes = company_indexes[ticker]["nodes"]

            scores, idx = index.search(vec, k=10)

            results.extend(nodes[i] for i in idx[0])

    return rerank(results, query)

def rerank(results, query):
    reranker = CrossEncoder("BAAI/bge-reranker-base")
    pairs = [
        (query, node["text"])
        for node in results
    ]

    rerank_scores = reranker.predict(pairs)

    ranked = sorted(
        zip(rerank_scores, results),
        key=lambda x: x[0],
        reverse=True
    )

    results = [node for score, node in ranked[:8]]
    return results

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
2. Every factual claim must be attributed to a specific source chunk, e.g. [Source 1].
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
