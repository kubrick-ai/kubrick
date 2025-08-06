import os
from config import get_secret, setup_logging, get_db_config
from vector_db_service import VectorDBService
from response_utils import (
    ErrorCode,
    build_error_response,
    build_success_response,
)
from s3_utils import add_presigned_urls

# Environment variables
SECRET_NAME = os.getenv("SECRET_NAME", "kubrick_secret")
PRESIGNED_URL_EXPIRY = int(os.getenv("PRESIGNED_URL_EXPIRY", "86400"))
SECRET = get_secret(SECRET_NAME)
DB_CONFIG = get_db_config(SECRET)
vector_db = VectorDBService(DB_CONFIG)


def lambda_handler(event, context):
    logger = setup_logging()
    try:
        logger.debug(f"event={event}")
        query_params = event.get("queryStringParameters") or {}
        limit = int(query_params.get("limit", 12))
        page = int(query_params.get("page", 0))

        logger.info("Fetching videos...")
        videos_data, total = vector_db.fetch_videos(page=page, limit=limit)

        logger.debug(f"Adding presigned URLs to videos: {videos_data}")
        add_presigned_urls(videos_data, PRESIGNED_URL_EXPIRY)

        logger.debug(f"Successfully added presigned urls: {videos_data}")
        return build_success_response(
            data=videos_data, metadata={"total": total, "limit": limit, "page": page}
        )

    except ValueError as e:
        logger.error(f"Error in lambda: {e}")
        return build_error_response(
            400, "Invalid parameters", ErrorCode.INVALID_REQUEST
        )

    except Exception as e:
        logger.error(f"Error in lambda: {e}")
        return build_error_response(500, "Internal server error")
