# Rag solution

To get started:
1. Activate/create virtual env:
    - `python3.11 -m venv .venv`
    - `source .venv/bin/activate`
2. Install requirements.txt: `pip install -r backend/requirements.txt`
3. Start ollama and load in ollama model:
    - `ollama serve`
    - `ollama pull qwen3:8b`
4. Start backend server: `python3.11 backend/server.py`
    - runs on http://localhost:5000/
5. Start frontend server: 
    - run `cd frontend` && `npm install` && `npm run dev`
    - runs on http://localhost:5001/ (or 5002, 5003 etc if others not available)

## Indexing:

To run the indexing pipeline, use `indexing.py` with optional arguments:
- `python3.11 indexing.py` runs full indexing pipeline (generates per-company and global indexes and recreates companies.json)
- `python3.11 indexing.py --no-indexing` or `python3.11 indexing.py -i` only runs recreation of companies.json
- `python3.11 indexing.py --no-company-map` or `python3.11 indexing.py -c` only runs indexing

Source code: indexing.py and company_lookup.py

## Testing backend:
```
curl -X POST http://127.0.0.1:5000/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What are the main risks facing Apple and Tesla?"}'
```

## Final Prompt Structure:
```
You are a financial research assistant that answers questions
using only SEC EDGAR filing excerpts provided to you. You do not give investment
advice or recommendations — only factual information grounded in the filings. 

Rules:
1. Use ONLY the provided context. Do not use prior knowledge about these companies.
2. Every factual claim must be attributed to a specific source chunk's file name, e.g. [AAPL_10K_2024Q3_2024-11-01_full.txt].
3. If chunks come from different companies or fiscal periods, never blend their data 
   together unless the question explicitly asks for a comparison — and if you do 
   compare, label each figure with its company and period.
4. If the context only partially answers the question, answer the part you can and 
   explicitly state what's missing.
5. If the context doesn't address the question at all, say so plainly — don't guess.
6. Never invent a source number that wasn't given to you.

Context:
{context}

Question:
{query}

Format: Use Markdown for formatting. For sources, remember to use the file name of the source chunk, e.g. [AAPL_10K_2024Q3_2024-11-01_full.txt].

At the start of your answer, provide a concise summary of the main points in the rest of the response. Focus on the actual content and mention specific points in your summary. The summary should not exceed 2 sentences in length.
```

## Quality Evaluation

See [Quality Evaluation](QUALITY_EVAL.md)

## Example Prompts
- "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"
- "How has NVIDIA's revenue and growth outlook changed over the last two years?"
- "What regulatory risks do the major pharmaceutical companies face, and how are they addressing them?"

