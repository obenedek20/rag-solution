import os
from llama_index.core import SimpleDirectoryReader
from generate_response import ask_llm
import json

"""
Idea: create a per-company FAISS index and then if any company names are found in the query
`x in c for c in companies` then we only use per-company index
"""


def extract_company(file_name):
    return file_name.split("_")[0]

companies = set()

print("Loading documents from edgar_corpus...")
documents = SimpleDirectoryReader("edgar_corpus").load_data()

for doc in documents:
    file_name = doc.metadata.get("file_name", "")
    companies.add(extract_company(file_name))

companies = sorted(companies)

print(companies)

resp = ask_llm("Take in this list of company tickers and respond with a json list of the tickers and their corresponding company names and common aliases (many if there are multiple common ones) for the company - the goal is to validate against a user input and see whether the user input contains any of these companies. If a ticker is not found, return 'Unknown' for the company name. Note that MS means Morgan Stanley, not Microsoft. The list of tickers is: " + ", ".join(companies))

print(resp)
resp = json.loads(resp) # convert to proper format

with open("companies.json", "w") as f: # create node file that stores text, metadata
    json.dump(
        resp,
        f,
        indent=2
    )