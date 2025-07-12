from flask import (
    Flask,
    jsonify,
    request,
)
import os
import embed
import vector_db


app = Flask(__name__)


@app.route("/health")
def health():
    return "", 200


@app.route("/search", methods=("POST",))
def search():
    """
    Expects a JSON body with the following properties:
        query_text: string,
        page_limit: integer (optional)
        min_similarity: float (optional)
    """
    request_data = request.get_json()

    if not request_data:
        return jsonify(
            {
                "error": "Invalid request body - must be a JSON object with 'query_text' parameter."
            }
        ), 400

    query_text = request_data.get("query_text")
    page_limit = request_data.get("page_limit")
    min_similarity = request_data.get("min_similarity")
    text_embedding = embed.extract_text_features(query_text)

    results = vector_db.find_similar(text_embedding, page_limit, min_similarity)

    data = {
        "data": results,
    }
    return jsonify(data)


# Route for video ingest tasks
@app.route("/tasks", methods=("GET", "POST"))
def tasks():
    if request.method == "GET":
        data = {
            "tasks": [{"id": "1234"}],
        }
        return jsonify(data)

    else:
        data = {
            "id": "1234",
        }
        return jsonify(data), 201


if __name__ == "__main__":
    if os.environ.get("FLASK_ENV") == "production":
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)
