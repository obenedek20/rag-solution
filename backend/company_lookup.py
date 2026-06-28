"""
Helper functions for company lookup and entity extraction from user queries
"""

import json
from rapidfuzz import process, fuzz
import re
import os
from llama_index.core import SimpleDirectoryReader
from ollama import chat

######################################################
# Creates companies.json from edgar_corpus
# Used inside indexing.py
######################################################

# Grabs company ticker from corpus file name
def extract_company(file_name):
    return file_name.split("_")[0]

# loads documents from corpus, gets ticker from file name, and queries LLM for list of company names and aliases
# saves results to companies.json
def retrieve_companies_from_tickers():
    companies = set()

    print("Loading documents from edgar_corpus...")
    documents = SimpleDirectoryReader("edgar_corpus").load_data()

    for doc in documents:
        file_name = doc.metadata.get("file_name", "")
        companies.add(extract_company(file_name))

    companies = sorted(companies)

    print(companies)

    resp = ask_llm("""Take in this list of company tickers and respond with the tickers and their 
    corresponding company names and common aliases (many if there are multiple common ones) for the company - 
    the goal is to validate against a user input and see whether the user input contains any of these companies. 
    If a ticker is not found, return 'Unknown' for the company name. Note that MS means Morgan Stanley, not Microsoft. 
    The output format should be a list of objects, each object containing the following fields: 'ticker', 'company', and 'aliases' (a list of strings).
    The list of tickers is: """ + ", ".join(companies))

    print(resp)
    resp = json.loads(resp) # convert to proper format

    with open("companies.json", "w") as f: # create node file that stores text, metadata
        json.dump(
            resp,
            f,
            indent=2
        )

######################################################
# Assumings companies.json has already been created
# Used inside generate.py to extract entities 
# from user query
######################################################

# Creates entity map from companies.json to search by company name/alias and return ticker (avoids LLM call for generation step)
def build_entity_map():
    """
    Creates map:

    "apple" → AAPL
    "iphone" → AAPL
    "facebook" → META
    "msft" → MSFT
    "microsoft" → MSFT
    """
    with open("companies.json", "r") as f:
        data = json.load(f)

    entity_map = {}

    for item in data:
        print(f"Processing item: {item}")
        ticker = item["ticker"]
        company = item["company"]
        aliases = item.get("aliases", [])

        # company name
        entity_map[company.lower()] = ticker

        # aliases only
        for a in aliases:
            entity_map[a.lower()] = ticker

    return entity_map

# normalize text for better matching
def normalize(text):
    text = text.lower()
    text = re.sub(r"\b(inc|inc\.|corp|corporation|co|company)\b", "", text)
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# find available company names in query (skip too-short aliases)
def extract_entities_hybrid(query, ENTITY_MAP):
    query_n = normalize(query)

    results = set()

    for alias, ticker in ENTITY_MAP.items():
        alias_n = normalize(alias)

        # skip too-short aliases (prevents MA / T-like issues)
        if len(alias_n) < 3:
            continue

        # word-boundary match only
        if re.search(rf"\b{re.escape(alias_n)}\b", query_n):
            results.add(ticker)

    return list(results)

# True if should use global search, not company specific - search global based on keywords (manually configured) or lack of tickers
def should_use_global(query, ENTITY_MAP, tickers):
    # no entities found
    if len(tickers) == 0:
        return True

    # generic query patterns → global
    global_keywords = [
        "overall", "market",
        "all companies",
        "which company",
        "best", "worst"
    ]

    q = query.lower()

    # use global if any global keywords present in query
    if any(k in q for k in global_keywords):
        return True

    return False


# Decide on global or per-company rag search
def route(query, ENTITY_MAP):
    tickers = extract_entities_hybrid(query, ENTITY_MAP)
    print(f"Extracted tickers: {tickers}")
    use_global = should_use_global(query, ENTITY_MAP, tickers)

    if use_global:
        return {
            "mode": "global",
            "tickers": []
        }

    return {
        "mode": "entity",
        "tickers": tickers
    }

######################################################
# ask_llm function used in company_lookup.py and 
# generate.py. Queries ollama llm
######################################################

# query ollama LLM with prompt and return response
def ask_llm(prompt):
    response = chat(
        model="qwen3:8b",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response["message"]["content"]
