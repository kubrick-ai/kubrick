import os
from config import get_secret, setup_logging, get_db_config
from vector_db_service import VectorDBService
from response_utils import (
    ErrorCode,
    build_error_response,
    build_options_response,
    build_success_response,
)

# Environment variables
SECRET_NAME = os.getenv("SECRET_NAME", "kubrick_secret")
DEFAULT_TASK_LIMIT = int(os.getenv("DEFAULT_TASK_LIMIT", "10"))
MAX_TASK_LIMIT = int(os.getenv("MAX_TASK_LIMIT", "50"))
DEFAULT_TASK_PAGE = int(os.getenv("DEFAULT_TASK_PAGE", "0"))


def lambda_handler(event, context):
    logger = setup_logging()
    SECRET = get_secret(SECRET_NAME)
    DB_CONFIG = get_db_config(SECRET)

    # # Handle preflight request (CORS)
    if event.get("httpMethod") == "OPTIONS":
        return build_options_response()

    vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)
    query_params = event.get("queryStringParameters") or {}
    logger.info(f"Received query params: {event.get('queryStringParameters')}")

    try:
        limit = max(
            1,
            min(
                int(query_params.get("limit", DEFAULT_TASK_LIMIT)),
                MAX_TASK_LIMIT,
            ),
        )
        page = max(0, int(query_params.get("page", DEFAULT_TASK_PAGE)))
    except ValueError:
        return build_error_response(
            status_code=400,
            message="Invalid 'limit' or 'page' parameter",
            error_code=ErrorCode.VALIDATION_ERROR,
        )

    try:
        tasks, total = vector_db_service.fetch_tasks(page=page, limit=limit)
        logger.info(f"{len(tasks)} tasks successfully fetched")

        return build_success_response(
            tasks,
            metadata={"limit": limit, "page": page, "total": total},
        )

    except Exception as e:
        logger.exception(f"Unhandled error in lambda_handler: {e}")
        return build_error_response(500, "Internal server error")
