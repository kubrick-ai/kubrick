import os
import boto3
import logging
import urllib.parse
from config import load_config, get_secret
from vector_db_service import VectorDBService
from utils import is_valid_video_file

s3 = boto3.client("s3")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        config = load_config()
        secret = get_secret(config)

        db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "database": os.getenv("DB_NAME", "kubrick"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": secret["DB_PASSWORD"],
            "port": int(os.getenv("DB_PORT", 5432)),
        }

        db = VectorDBService(db_params=db_config, logger=logger)

        for record in event.get("Records", []):
            event_name = record.get("eventName", "")
            bucket = record.get("s3", {}).get("bucket", {}).get("name")
            key = urllib.parse.unquote_plus(
                record.get("s3", {}).get("object", {}).get("key", "")
            ).strip()

            if not bucket or not key:
                logger.warning("Missing bucket or key in S3 event record")
                continue

            logger.info(
                f"Processing event: {event_name}, S3 bucket: {bucket}, S3 key: {key}"
            )

            if not is_valid_video_file(key):
                logger.info(f"Ignoring non-video object S3 key: {key}")
                continue

            results = db.fetch_video(bucket=bucket, key=key)

            if results:
                deleted = db.delete_video(bucket=bucket, key=key)
                if deleted:
                    logger.info(
                        f"Deleted data for S3 key:{key} from S3 bucket: {bucket} from database."
                    )
                else:
                    logger.warning(
                        f"Failed to delete data for S3 key:{key} from S3 bucket: {bucket}. It might have been already removed."
                    )
            else:
                logger.info(
                    f"No data found in DB for deleted S3 object [bucket: {bucket}, key: {key}]"
                )

    except Exception as e:
        logger.exception("Unhandled exception in Lambda handler")
