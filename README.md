# Rag solution

To get started:
1. Activate/create virtual env:
    - `python3.11 -m venv .venv`
    - `source .venv/bin/activate`
2. Install requirements.txt: `pip install -r backend/requirements.txt`
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

## Backend: Retrieval and Generation

- Start backend server: `python3.11 backend/server.py`

Note: runs on http://localhost:5000/

### Testing backend:
```
curl -X POST http://127.0.0.1:5000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the main risks facing Apple and Tesla?"}'
```

Source code: generate.py

## Frontend

Steps:
1. run `cd frontend`
2. run `npm install`
3. run `npm run dev`

Server runs on http://localhost:5001/
