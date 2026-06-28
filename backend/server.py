from flask import Flask, jsonify, request
from generate import process_query
from company_lookup import build_entity_map

app = Flask(__name__)
ENTITY_MAP = build_entity_map()

@app.get("/query")
def query():
    query = request.args.get("query")  # single string parameter

    if not query:
        return jsonify({
            "error": "Missing required parameter: query"
        }), 400

    response = process_query(query, ENTITY_MAP)
    return jsonify({
        "response": response,
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)