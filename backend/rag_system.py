"""
Best ways to enhance output from RAG system
    Chunking: in this case for edgar corpus, should be natural breaks in documents (semantic)
    Retriever tuning: tune top-K rankings and confidence scores
    Prompt side: potentially limit the end prompt sent to LLM - can optimize responses
        - need to tune the information we add to prompt from RAG system

Design
    Database: FAISS (good for local development)
    Embedding models: sentence_transformers
        BAAI/bge-small-en-v1.5
        BAAI/bge-base-en-v1.5
        BAAI/bge-large-en-v1.5
        intfloat/e5-base-v2
        intfloat/e5-large-v2

Stack
    LlamaIndex (Document parsing and chunking)
        ↓
    Sentence Transformers (Embeddings)
            ↓
    FAISS (vector db)
            ↓
    CrossEncoder reranker (re-ranking)
            ↓
    LLM (Ollama)

TODO:
    - defend each design choice
    - code up the design
    - iteratively test design
"""

from ollama import chat

prompt = "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"

response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print(response["message"]["content"])
