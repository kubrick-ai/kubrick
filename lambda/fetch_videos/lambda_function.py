import json
import boto3
from config import load_config, get_secret, setup_logging, get_db_config
from vector_db_service import VectorDBService


def generate_presigned_url(
    logger, bucket: str, key: str, expires_in: int = 3600
) -> str:
    s3 = boto3.client("s3")
    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        return None


def lambda_handler(event, context):
    logger = setup_logging()
    config = load_config()
    SECRET = get_secret(config)
    DB_CONFIG = get_db_config(SECRET)

    vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)

    query_params = event.get("queryStringParameters") or {}
    limit = int(query_params.get("limit", 12))
    page = int(query_params.get("page", 0))

    try:
        result = vector_db_service.fetch_videos(page=page, limit=limit)

        videos = []
        for video in result["videos"]:
            video_data = {
                "id": video["id"],
                "filename": video["filename"],
                "duration": video["duration"],
                "created_at": (
                    video["created_at"].isoformat() if video["created_at"] else None
                ),
                "updated_at": (
                    video["updated_at"].isoformat() if video["updated_at"] else None
                ),
                "height": video["height"],
                "width": video["width"],
                "s3_bucket": video["s3_bucket"],
                "s3_key": video["s3_key"],
            }

            if video["s3_bucket"] and video["s3_key"]:
                video_data["url"] = generate_presigned_url(
                    logger,
                    video["s3_bucket"],
                    video["s3_key"],
                    config["presigned_url_expiry"],
                )

            videos.append(video_data)

        response_body = {
            "videos": videos,
            "total": result["total"],
        }

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps(response_body),
        }

    except Exception as e:
        logger.error(f"Error in lambda: {e}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps({"error": str(e)}),
        }
