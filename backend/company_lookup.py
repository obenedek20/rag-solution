import json
from rapidfuzz import process, fuzz
import re
import json

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

    if any(k in q for k in global_keywords):
        return True

    return False

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
