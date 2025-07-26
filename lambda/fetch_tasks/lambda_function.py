import json
from vector_db_service import VectorDBService
from config import load_config, get_secret, setup_logging, get_db_config


def lambda_handler(event, context):
    logger = setup_logging()
    config = load_config()
    SECRET = get_secret(config)
    DB_CONFIG = get_db_config(SECRET)

    # # Handle preflight request (CORS)
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps({}),
        }

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
        return {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps({"error": "Invalid 'limit' or 'page' parameter"}),
        }

    try:
        tasks = vector_db_service.fetch_tasks(page=page, limit=limit)
        logger.info(f"{len(tasks)} tasks successfully fetched")

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps(
                {
                    "data": tasks,
                    "metadata": {
                        "limit": limit,
                        "page": page,
                        "total": len(tasks),
                    },
                }
            ),
        }

    except Exception as e:
        logger.exception(f"Unhandled error in lambda_handler")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps({"error": str(e)}),
        }
