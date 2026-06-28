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