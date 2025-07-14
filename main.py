from flask import (
    Flask,
    jsonify,
    request,
)
import os
from search_routes import search_bp


app = Flask(__name__)
app.register_blueprint(search_bp)


@app.route("/health")
def health():
    return "", 200


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
