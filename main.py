from flask import (
    Flask,
    jsonify,
    request,
)
import os
from task_store import TaskStore
from worker import start_background_task, task_store

app = Flask(__name__)

@app.route("/health")
def health():
    return "", 200


@app.route("/search", methods=("POST",))
def search():
    data = {
        "results": [],
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
