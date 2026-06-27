from ollama import chat
import faiss
import numpy as np
import json
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from company_lookup import route, build_entity_map
import os

###############################
# Querying (Online)
###############################
embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5",
    device="mps" # more efficient when using Apple Silicon
)

ENTITY_MAP = build_entity_map()
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

# Retrieve top-K relevant nodes
# def retrieve(query, k=5):
#     q_emb = embed_query(query)

#     scores, indices = index.search(q_emb, k)

#     results = []
#     # for idx in indices[0]:
#     #     results.append(node_data[idx])
#     results = [node_data[i] for i in indices[0]]

#     return results
def retrieve(query):

    route_info = route(query, ENTITY_MAP)

    vec = embed_query(query)

    results = []

    # CASE 1: GLOBAL
    if route_info["mode"] == "global":
        with open("nodes.json", "r") as f:
            all_nodes = json.load(f)
        global_index = faiss.read_index("global.index.faiss") # binary vector db with embeddings of size n
        scores, idx = global_index.search(vec, k=10)
        results = [all_nodes[i] for i in idx[0]]

    # CASE 2: PER-COMPANY
    else:
        company_indexes = retrieve_company_indexes()
        for ticker in route_info["tickers"]:
            index = company_indexes[ticker]["index"]
            nodes = company_indexes[ticker]["nodes"]

            scores, idx = index.search(vec, k=5)

            results.extend(nodes[i] for i in idx[0])

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
You are a helpful assistant. Use ONLY the context below.

Context:
{context}

Question:
{query}

If the answer is not in the context, say you don't know.
"""

def ask_llm(prompt):
    response = chat(
        model="qwen3:8b",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response["message"]["content"]


if __name__ == "__main__":

    prompt = "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"

    print(f"Query: {prompt}")
    print(f"Retrieving relevant nodes...")
    results = retrieve(prompt)
    print(f"Retrieved {len(results)} nodes.")
    rag_prompt = build_prompt(prompt, results)
    print("Sending prompt to LLM...")
    print("Prompt: " + rag_prompt)
    response = ask_llm(rag_prompt)
    print("Response: " + response)
