import os
import logging
import time
import botocore.exceptions
import urllib.parse
import json

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
    ".mpeg",
    ".mpg",
    ".mpe",
    ".m4v",
    ".3gp",
    ".ogv",
    ".ts",
    ".mxf",
}

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def is_valid_video_file(s3_key):
    valid = has_valid_file_extension(s3_key)
    if valid:
        logger.info(f"File '{s3_key}' has a valid video extension.")
    else:
        logger.warning(f"File '{s3_key}' does not have a valid video extension.")
    return valid


def has_valid_file_extension(s3_key):
    _, ext = os.path.splitext(s3_key.lower())
    logger.debug(f"Checking file extension: '{ext}'")
    return ext in VIDEO_EXTENSIONS


def wait_for_file(s3_client, bucket, key, retries=3, delay=2):
    for attempt in range(retries):
        try:
            logger.info(
                f"Checking if file exists: s3://{bucket}/{key} (attempt {attempt + 1}/{retries})"
            )
            s3_client.head_object(Bucket=bucket, Key=key)
            logger.info("File found in S3")
            return True
        except botocore.exceptions.ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                logger.warning(f"File not found. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Unexpected error while checking file existence: {e}")
                raise
    logger.warning("File still not found after all retries")
    return False


# TODO: This will eventually have to be moved to the embed service layer
def create_embedding_request(config, client, url):
    logger.info(f"Creating embedding task using model: {config['model_name']}")
    try:
        task = client.embed.tasks.create(
            model_name=config["model_name"],
            video_url=url,
            video_clip_length=config["clip_length"],
            video_embedding_scope=config["video_embedding_scopes"],
        )
        logger.info(f"Embedding task created with ID: {task.id}")
        return task.id
    except Exception as e:
        logger.error(f"Failed to create embedding request: {e}")
        raise


def extract_s3_info(event):
    records = event.get("Records", [])
    if not records:
        raise ValueError("No Records found in event")

    record = records[0]
    bucket = record.get("s3", {}).get("bucket", {}).get("name")
    key = urllib.parse.unquote_plus(
        record.get("s3", {}).get("object", {}).get("key", "")
    ).strip()

    if not bucket or not key:
        raise ValueError("Missing bucket or key in event")

    return bucket, key


def persist_task_metadata(db, metadata, fallback_status="failed"):
    try:
        db.store_task(metadata)
        logger.info(f"Task metadata stored in DB: {metadata}")
    except Exception as e:
        logger.error(f"Failed to store task metadata: {e}")
        fallback = dict(metadata)
        fallback["status"] = fallback_status
        logger.error(f"Fallback data: {json.dumps(fallback)}")
