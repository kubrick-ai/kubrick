import json
import boto3
import time
import botocore.exceptions
import os
import logging
import utils
import urllib.parse
from twelvelabs import TwelveLabs
from config import load_config, get_secret, setup_logging, get_db_config
from vector_db_service import VectorDBService


def wait_for_file(
    s3_client, bucket, key, retries=3, delay=2, logger=logging.getLogger()
):
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


def persist_task_metadata(
    db, metadata, fallback_status="failed", logger=logging.getLogger()
):
    try:
        db.store_task(metadata)
        logger.info(f"Task metadata stored in DB: {metadata}")
    except Exception as e:
        logger.error(f"Failed to store task metadata: {e}")
        fallback = dict(metadata)
        fallback["status"] = fallback_status
        logger.error(f"Fallback data: {json.dumps(fallback)}")


def lambda_handler(event, context):
    s3 = boto3.client("s3")
    sqs = boto3.client("sqs")
    logger = setup_logging()
    config = load_config()
    SECRET = get_secret(config)
    DB_CONFIG = get_db_config(SECRET)
    QUEUE_URL = os.environ["QUEUE_URL"]

    logger.info("Lambda handler invoked")

    tl_client = TwelveLabs(api_key=SECRET["TWELVELABS_API_KEY"])
    vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)

    try:
        bucket, key = extract_s3_info(event)
        logger.info(f"Extracted S3 bucket: {bucket}, key: {key}")

        if key.endswith("/"):
            logger.info(f"Ignoring folder creation event for key: {key}")
            return {"status": "ignored", "reason": "S3 event is a folder creation"}

        if not utils.is_valid_video_file(key):
            raise ValueError("File is not a video or the video format is not supported")
        logger.info("Validated video file type")

        if not wait_for_file(
            s3,
            bucket,
            key,
            config["file_check_retries"],
            config["file_check_delay_sec"],
            logger,
        ):
            raise FileNotFoundError(f"File s3://{bucket}/{key} not found after retries")

        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=config["presigned_url_ttl"],
        )
        logger.info(
            f"Presigned URL generated (expires in {config['presigned_url_ttl']} seconds)"
        )

        task_id = utils.create_embedding_request(
            config=config, client=tl_client, url=presigned_url
        )

        message_body = json.dumps(
            {
                "twelvelabs_video_embedding_task_id": task_id,
                "s3_bucket": bucket,
                "s3_key": key,
            }
        )
        sqs_response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message_body)
        sqs_message_id = sqs_response["MessageId"]
        logger.info(f"SQS message sent with ID: {sqs_message_id}")

        metadata = {
            "sqs_message_id": sqs_message_id,
            "s3_bucket": bucket,
            "s3_key": key,
            "status": "processing",
            "twelvelabs_task_id": task_id,
        }
        persist_task_metadata(vector_db_service, metadata, logger=logger)

        logger.info("Lambda execution completed successfully")
        return {
            "status": "success",
            "task_id": task_id,
            "sqs_message_id": sqs_message_id,
            "s3_bucket": bucket,
            "s3_key": key,
        }

    except Exception as e:
        logger.exception("Unhandled exception occurred")

        metadata = {
            "sqs_message_id": locals().get("sqs_message_id"),
            "s3_bucket": locals().get("bucket"),
            "s3_key": locals().get("key"),
            "status": "failed",
        }
        persist_task_metadata(
            vector_db_service, metadata, fallback_status="failed", logger=logger
        )

        return {"status": "error", "message": str(e)}
