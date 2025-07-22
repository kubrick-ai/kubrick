import json
import boto3
import os
import time
import logging
import urllib.parse
import botocore.exceptions
from twelvelabs import TwelveLabs

QUEUE_URL = os.environ["QUEUE_URL"]
with open("config.json") as f:
    CONFIG = json.load(f)

s3 = boto3.client("s3")
sqs = boto3.client("sqs")
secretsmanager = boto3.client("secretsmanager")
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_api_key():
    secret_name = CONFIG["secret_name"]
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        return secret["TWELVELABS_API_KEY"]
    except Exception as e:
        logger.error(f"Failed to retrieve secret: {e}")
        raise


client = TwelveLabs(api_key=get_api_key())


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
                logger.error(f"Unexpected error while checking file: {e}")
                raise
    logger.warning("File still not found after retries")
    return False


def create_embedding_request(url, start_offset=None, end_offset=None):
    embedding_request = client.embed.task.create(
        model_name=CONFIG["model_name"],
        video_url=url,
        video_clip_length=CONFIG["clip_length"],
        video_start_offset_sec=start_offset,
        video_end_offset_sec=end_offset,
        video_embedding_scopes=CONFIG["video_embedding_scopes"],
    )
    return embedding_request.id


def lambda_handler(event, context):
    try:
        record = event.get("Records", [{}])[0]
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
            CONFIG["file_check_retries"],
            CONFIG["file_check_delay_sec"],
        ):
            raise Exception(f"File s3://{bucket}/{key} not found after retries.")

        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=CONFIG["presigned_url_expiry"],
        )

        task_id = create_embedding_request(url=presigned_url)

        message_body = json.dumps(
            {
                "twelvelabs_video_embedding_task_id": task_id,
                "bucket": bucket,
                "key": key,
            }
        )

        sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message_body)

        logger.info(f"Task ID: {task_id} for video: {key} has been added to the queue")
        return {"status": "ok"}

    except Exception as e:
        logger.exception("Unhandled error in lambda_handler")
        return {"status": "error", "message": str(e)}
