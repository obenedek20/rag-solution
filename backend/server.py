from flask import Flask, jsonify, request
from generate import process_query
from company_lookup import build_entity_map
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
ENTITY_MAP = None

@app.post("/query")
def query():
    data = request.get_json(silent=True) or {}

    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing required field: query"}), 400

    response = process_query(query, ENTITY_MAP)
    return jsonify({"response": response})

if __name__ == "__main__":
    ENTITY_MAP = build_entity_map()
    app.run(host="127.0.0.1", port=5000, debug=True)