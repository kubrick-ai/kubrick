import logging
import os
from config import load_config
from vector_db_service import VectorDBService
from response_utils import (
    build_error_response,
    build_success_response,
    generate_presigned_url,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    config = load_config()
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "database": "kubrick",
        "user": "postgres",
        "password": os.getenv("DB_PASSWORD"),
        "port": 5432,
    }

    query_params = event.get("queryStringParameters") or {}
    limit = int(query_params.get("limit", 12))
    page = int(query_params.get("page", 0))

    try:
        vector_db = VectorDBService(DB_CONFIG)
        videos_data, total = vector_db.fetch_videos(page=page, limit=limit)
        for video in videos_data:
            if video.get("s3_bucket") and video.get("s3_key"):
                video["url"] = generate_presigned_url(
                    video["s3_bucket"], video["s3_key"], config["presigned_url_expiry"]
                )
        build_success_response(data=videos_data, metadata={"total": total})

    except Exception as e:
        logger.error(f"Error in lambda: {e}")
        return build_error_response(500, "Internal server error")
