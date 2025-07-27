from config import load_config, get_secret, setup_logging, get_db_config
from vector_db_service import VectorDBService
from response_utils import (
    build_error_response,
    build_success_response,
    generate_presigned_url,
)


def lambda_handler(event, context):
    logger = setup_logging()
    try:
        config = load_config()
        SECRET = get_secret(config)
        DB_CONFIG = get_db_config(SECRET)
        logger.debug(f"event={event}")
        query_params = event.get("queryStringParameters") or {}
        limit = int(query_params.get("limit", 12))
        page = int(query_params.get("page", 0))

        vector_db = VectorDBService(DB_CONFIG)
        logger.info("Fetching videos...")
        videos_data, total = vector_db.fetch_videos(page=page, limit=limit)
        logger.debug(f"videos={videos_data}")
        for video in videos_data:
            if video.get("s3_bucket") and video.get("s3_key"):
                video["url"] = generate_presigned_url(
                    video["s3_bucket"], video["s3_key"], config["presigned_url_expiry"]
                )
        return build_success_response(
            data=videos_data, metadata={"total": total, "limit": limit, "page": page}
        )

    except Exception as e:
        logger.error(f"Error in lambda: {e}")
        return build_error_response(500, "Internal server error")
