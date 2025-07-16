from flask import Blueprint, jsonify, request
from app.tasks import Task, task_store, start_background_task

from app.services.embed_service import EmbedService
from app.services.vector_db_service import VectorDBService


def create_tasks_bp(embed_service: EmbedService, vector_db_service: VectorDBService):
    tasks_bp = Blueprint("tasks", __name__)

    @tasks_bp.route("/tasks", methods=("GET", "POST"))
    def task():
        if request.method == "GET":
            page = int(request.args.get("page", 1))
            page_limit = min(int(request.args.get("page_limit", 10)), 50)
            tasks = task_store.list_tasks(page, page_limit)

            return jsonify({
                "data": [{
                    "id": task.id,
                    "status": task.status,
                    "video_url": task.video_url,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "error": task.error,
                    "metadata": task.metadata,
                } for task in tasks],
            }), 201

        else:
            video_url = request.form.get("video_url")
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
    @tasks_bp.route("/tasks/<task_id>", methods=["GET"])
    def get_task_status(task_id):
        task = task_store.get_task(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({
            "task_id": task.id,
            "status": task.status,
            "error": task.error,
        })
    
    return tasks_bp
