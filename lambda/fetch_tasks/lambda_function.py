import json
import os
import logging
from config import load_config, get_secret
from vector_db_service import VectorDBService
from response_utils import (
    ErrorCode,
    build_error_response,
    build_options_response,
    build_success_response,
)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    # # Handle preflight request (CORS)
    if event.get("httpMethod") == "OPTIONS":
        return build_options_response

    config = load_config()
    SECRET = get_secret(config)
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "kubrick"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": SECRET["DB_PASSWORD"],
        "port": 5432,
    }

    db = VectorDBService(db_params=DB_CONFIG, logger=logger)
    query_params = event.get("queryStringParameters") or {}
    logger.info(f"Received query params: {event.get('queryStringParameters')}")

    try:
        limit = max(
            1,
            min(
                int(query_params.get("limit", config["default_limit"])),
                config["max_limit"],
            ),
        )
        page = max(0, int(query_params.get("page", config["default_page"])))
    except ValueError:
        return build_error_response(
            status_code=400,
            message="Invalid 'limit' or 'page' parameter",
            error_code=ErrorCode.VALIDATION_ERROR,
        )

    try:
        tasks = db.fetch_tasks(page=page, limit=limit)
        tasks_total = db.fetch_tasks_total()
        logger.info(f"{len(tasks)} tasks successfully fetched")

        return build_success_response(
            tasks,
            metadata={"limit": limit, "page": page, "total": tasks_total},
        )

    except Exception as e:
        logger.exception(f"Unhandled error in lambda_handler: {e}")
        return build_error_response(500, "Internal server error")
