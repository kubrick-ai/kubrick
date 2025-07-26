import json
import boto3
import os
import logging
import utils
from twelvelabs import TwelveLabs
from config import load_config, get_secret
from vector_db_service import VectorDBService

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Lambda handler invoked")

    config = load_config()
    SECRET = get_secret(config)

    QUEUE_URL = os.environ["QUEUE_URL"]
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "kubrick"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": SECRET["DB_PASSWORD"],
        "port": 5432,
    }

    tl_client = TwelveLabs(api_key=SECRET["TWELVELABS_API_KEY"])
    db = VectorDBService(db_params=DB_CONFIG, logger=logger)

    if "ObjectCreated:Copy" in event:
        logger.info(f"Ignoring file copy event for key: {key}")
        return {"status": "ignored", "reason": "File copy event"}

    try:
        bucket, key = utils.extract_s3_info(event)
        logger.info(f"Extracted S3 bucket: {bucket}, key: {key}")

        if key.endswith("/"):
            logger.info(f"Ignoring folder creation event for key: {key}")
            return {"status": "ignored", "reason": "S3 event is a folder creation"}

        if not utils.is_valid_video_file(key):
            raise ValueError("File is not a video or the video format is not supported")
        logger.info("Validated video file type")

        if not utils.wait_for_file(
            s3,
            bucket,
            key,
            config["file_check_retries"],
            config["file_check_delay_sec"],
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
        utils.persist_task_metadata(db, metadata)

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
        utils.persist_task_metadata(db, metadata, fallback_status="failed")

        return {"status": "error", "message": str(e)}
