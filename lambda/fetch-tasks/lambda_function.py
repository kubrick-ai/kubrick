import json
import os
import logging
from config import load_config, get_secret
from vector_db_service import VectorDBService


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
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
        tasks = db.fetch_tasks(page=page, limit=limit)
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
                        "total_tasks": len(tasks),
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
