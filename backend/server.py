from flask import Flask, jsonify, request
from generate_response import process_query

app = Flask(__name__)

@app.get("/query")
def query():
    query = request.args.get("query")  # single string parameter

    if not query:
        return jsonify({
            "error": "Missing required parameter: query"
        }), 400
    # prompt = "What are the primary risk factors facing Apple, Tesla, and JPMorgan, and how do they compare?"
    # prompt = "How has NVIDIA's revenue and growth outlook changed over the last two years?"
    # prompt = "What regulatory risks do the major pharmaceutical companies face, and how are they addressing them?"
    response = process_query(query)
    return jsonify({
        "response": response,
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)