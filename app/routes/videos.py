from app.services.vector_db_service import VectorDBService
from flask import Blueprint, jsonify, request


def create_videos_bp(vector_db_service: VectorDBService):
    videos_bp = Blueprint("videos", __name__)

    @videos_bp.route("/videos", methods=(["GET"]))
    # Route to fetch all videos in library
    def get_videos():
        page = int(request.args.get("page", 0))
        page_limit = min(int(request.args.get("page_limit", 10)), 50)
        videos = vector_db_service.fetch_videos(page, page_limit)

        data = {"data": videos}

        return (jsonify(data), 200)

    return videos_bp
