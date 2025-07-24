import json
import boto3
import os
import time
import logging
import urllib.parse
import botocore.exceptions
from twelvelabs import TwelveLabs
from config import load_config, get_secret

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def wait_for_file(s3_client, bucket, key, retries=3, delay=2):
    for attempt in range(retries):
        try:
            logger.info(f"Checking file existence attempt {attempt + 1}/{retries}")
            s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except botocore.exceptions.ClientError as e:
            code = e.response.get("Error", {}).get("Code")
            if code == "404":
                logger.warning(f"Attempt {attempt + 1}: File not found")
                time.sleep(delay)
            else:
                logger.error(
                    f"Unexpected error while checking file (Code: {code}): {e}"
                )
                raise
    logger.warning("File still not found after retries")
    return False


def create_embedding_request(config, client, url, start_offset=None, end_offset=None):
    try:
        return client.embed.tasks.create(
            model_name=config["model_name"],
            video_url=url,
            video_clip_length=config["clip_length"],
            video_embedding_scope=config["video_embedding_scopes"],
        ).id
    except Exception as e:
        logger.error(f"Failed to create embedding request: {e}")
        raise


def lambda_handler(event, context):
    config = load_config()
    SECRET = get_secret(config)
    tl_client = TwelveLabs(api_key=SECRET["TWELVELABS_API_KEY"])
    logger.info("Established TL client")
    QUEUE_URL = os.environ["QUEUE_URL"]

    try:
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

        if not wait_for_file(
            s3,
            bucket,
            key,
            config["file_check_retries"],
            config["file_check_delay_sec"],
        ):
            raise Exception(f"File s3://{bucket}/{key} not found after retries.")

        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=config["presigned_url_ttl"],
        )

        logger.info(
            f"Generated presigned URL for s3://{bucket}/{key}, available for {config['presigned_url_ttl']} seconds"
        )

        task_id = create_embedding_request(
            config=config, client=tl_client, url=presigned_url
        )

        message_body = json.dumps(
            {
                "twelvelabs_video_embedding_task_id": task_id,
                "s3_bucket": bucket,
                "s3_key": key,
            }
        )

        response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message_body)
        sqs_message_id = response["MessageId"]

        logger.info(
            f"Task ID: {task_id} for video: {key} has been added to the queue with message ID: {sqs_message_id}"
        )
        # TODO: Store in the DB the task with: sqs_message_id, s3_bucket, s3_key, status="processing"

        return {
            "status": "success",
            "task_id": task_id,
            "sqs_message_id": sqs_message_id,
            "s3_bucket": bucket,
            "s3_key": key,
        }

    except Exception as e:
        logger.exception("Unhandled error in lambda_handler")
        # TODO: Store in the DB errors with status "failed"
        return {"status": "error", "message": str(e)}
