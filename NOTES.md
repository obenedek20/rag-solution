Best ways to enhance output from RAG system
    Chunking: in this case for edgar corpus, should be natural breaks in documents (semantic)
        - Note: do not oversplit (can lose context), do not undersplit (too much context)
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

Ollama
    easy to use locally
    `ollama serve` to start ollama server
    `ollama pull qwen3:8b` to pull qwen3:8b model
    models include: qwen3:8b, llama3.1:8b

Stack
    LlamaIndex (Document parsing and chunking)
        ↓
    Sentence Transformers (Embeddings)
            ↓
    FAISS (vector db, similarity search)
            ↓
    CrossEncoder reranker (re-ranking)
            ↓
    LLM (Ollama)

Two stages:
    Indexing: Read documents, chunk them, create embeddings, and build a FAISS index.
    Querying (only one): Embed the question, retrieve the most relevant chunks, and send them to LLM

TODO:
- defend each design choice
- code up the design
    - try and collect results without re-ranking
    - add re-ranking and compare results
- iteratively test design
- Try to pre-process data:
    - Because this is an EDGAR corpus, I'd also recommend checking for duplicate or boilerplate text. Many filings repeat sections like legal disclaimers or standard headers. Removing those before indexing can reduce the number of chunks and improve retrieval quality.
- Make sure this can be run on localhost
    1. setup backend to response to api call
    2. frontend - simple but able to send out call, wait for sync response, show loading while waiting
- per company approach for rag search
    1. potentially eliminates the issue where one company does not have the chunks available
    2. risk: too much info for the LLM to handle (because we accidently select too many tickers)