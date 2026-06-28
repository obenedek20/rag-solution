# Rag solution

To get started:
1. Activate/create virtual env:
    - `python3.11 -m venv .venv`
    - `source .venv/bin/activate`
2. Install requirements.txt: `pip install -r requirements.txt`
3. Start ollama and load in ollama model:
    - `ollama serve`
    - `ollama pull qwen3:8b` or `ollama pull llama3.1:8b`
4. Start backend server: `python3.11 backend/server.py`

## Indexing:

Use `indexing.py` with optional arguments:
- `python3.11 indexing.py` runs full indexing pipeline (generates per-company and global indexes and recreates companies.json)
- `python3.11 indexing.py --no-indexing` or `python3.11 indexing.py -i` only runs recreation of companies.json
- `python3.11 indexing.py --no-company-map` or `python3.11 indexing.py -c` only runs indexing

Source code: indexing.py and company_lookup.py

## Retrieval and Generation

- Start backend server: `python3.11 backend/server.py`

Source code: generate.py