import os
import boto3
import logging
from config import load_config, get_secret
from vector_db_service import VectorDBService

s3 = boto3.client("s3")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
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

    try:
        for record in event.get("Records", []):
            s3_info = record["s3"]
            bucket = s3_info["bucket"]["name"]
            key = s3_info["object"]["key"]

            if db.fetch_video(bucket=bucket, key=key):
                db.delete_video(bucket=bucket, key=key)
            else:
                logger.info(f"S3 key: {key} from bucket: {bucket} doesn't exist in the database")

    except Exception as e:
        logger.exception("Unhandled exception occurred")