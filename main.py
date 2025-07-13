from flask import (
    Flask,
    jsonify,
    request,
)
import os
from task_store import task_store
from worker import start_background_task
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
# Get requests sends back a list of tasks
# Post requests will start the video ingesting part, just need to provide URL to video
@app.route("/tasks", methods=("GET", "POST"))
def tasks():
    if request.method == "GET":
        page = int(request.args.get("page", 1))
        page_limit = min(int(request.args.get("page_limit", 10)), 50)
        tasks = task_store.list_tasks(page, page_limit)

        return jsonify({
            "tasks": [{
                "task_id": task.id,
                "status": task.status,
                "video_url": task.video_url,
                "created_at": task.created_at,
                "completed_at": task.completed_at,
            } for task in tasks],
        })

    else:
        data = request.get_json()
        video_url = data.get("video_url")
        if not video_url:
            return jsonify({"error": "Missing 'video_url' in request body"}), 400

        task = task_store.create_task(video_url)
        start_background_task(task.id, video_url)

        return jsonify({
            "id": task.id,
            "status": task.status,
            "video_url": task.video_url,
        }), 201

# Route to query for status of individual task
@app.route("/tasks/<task_id>", methods=["GET"])
def get_task_status(task_id):
    task = task_store.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({
        "task_id": task.id,
        "status": task.status,
        "error": task.error,
    })


if __name__ == "__main__":
    if os.environ.get("FLASK_ENV") == "production":
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)
