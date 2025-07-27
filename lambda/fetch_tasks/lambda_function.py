from config import load_config, get_secret, setup_logging, get_db_config
from vector_db_service import VectorDBService
from response_utils import (
    ErrorCode,
    build_error_response,
    build_options_response,
    build_success_response,
)


def lambda_handler(event, context):
    logger = setup_logging()
    config = load_config()
    SECRET = get_secret(config)
    DB_CONFIG = get_db_config(SECRET)

    # # Handle preflight request (CORS)
    if event.get("httpMethod") == "OPTIONS":
        return build_options_response

    vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)
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
        tasks, total = vector_db_service.fetch_tasks(page=page, limit=limit)
        logger.info(f"{len(tasks)} tasks successfully fetched")

        return build_success_response(
            tasks,
            metadata={"limit": limit, "page": page, "total": total},
        )

    except Exception as e:
        logger.exception(f"Unhandled error in lambda_handler: {e}")
        return build_error_response(500, "Internal server error")
