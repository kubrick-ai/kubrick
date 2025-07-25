import json
import logging
import boto3
import os
from config import load_config
from vector_db_service import VectorDBService

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def generate_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    s3 = boto3.client("s3")
    try:
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        return None


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
    limit = int(query_params.get("limit", 50))
    page = int(query_params.get("page", 0))

    try:
        vector_db = VectorDBService(DB_CONFIG)

        raw_videos = vector_db.fetch_videos(page=page, limit=limit)

        videos = []
        for video in raw_videos:
            video_data = {
                "id": video["id"],
                "filename": video["filename"],
                "duration": video["duration"],
                "created_at": video["created_at"].isoformat() if video["created_at"] else None,
                "updated_at": video["updated_at"].isoformat() if video["updated_at"] else None,
                "height": video["height"],
                "width": video["width"],
                "s3_bucket": video["s3_bucket"],
                "s3_key": video["s3_key"],
            }

            if video["s3_bucket"] and video["s3_key"]:
                video_data["url"] = generate_presigned_url(
                    video["s3_bucket"],
                    video["s3_key"],
                    config["presigned_url_expiry"]
                )

            videos.append(video_data)

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps(videos),
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