import os
import asyncio
import aioboto3
import urllib.parse
import time
import boto3
import botocore.exceptions
from botocore.config import Config
import logging

S3_REGION = os.getenv("S3_REGION")
S3_CLIENT_CONFIG = Config(
    region_name=S3_REGION,
    signature_version="s3v4",
    s3={"addressing_style": "virtual"},
)
logger = logging.getLogger()


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


def wait_for_file(
    bucket: str,
    key: str,
    retries: int,
    delay: int | float,
    logger=logging.getLogger(),
    s3_client=boto3.client("s3", region_name=S3_REGION, config=S3_CLIENT_CONFIG),
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


def generate_presigned_url(
    bucket: str,
    key: str,
    content_type: str = None,
    expires_in: int = 3600,
    client_method="get_object",
) -> str:
    return asyncio.run(
        generate_presigned_url_async(
            bucket, key, content_type, expires_in, client_method
        )
    )


async def generate_presigned_url_async(
    bucket: str,
    key: str,
    content_type: str = None,
    expires_in: int = 3600,
    client_method="get_object",
    session=aioboto3.Session(),
) -> str:
    async with session.client(
        "s3", region_name=S3_REGION, config=S3_CLIENT_CONFIG
    ) as s3_client:  # type: ignore (type error in aioboto3 library)
        try:
            params = {"Bucket": bucket, "Key": key}

            if content_type:
                params["ContentType"] = content_type

            url = await s3_client.generate_presigned_url(
                ClientMethod=client_method,
                Params=params,
                ExpiresIn=expires_in,
            )

            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise


def add_presigned_urls(items, expires_in: int = 3600):
    asyncio.run(add_presigned_urls_async(items, expires_in))


async def add_presigned_urls_async(items, expires_in):
    session = aioboto3.Session()
    for item in items:
        if item.get("s3_bucket") and item.get("s3_key"):
            item["url"] = await generate_presigned_url_async(
                bucket=item["s3_bucket"],
                key=item["s3_key"],
                expires_in=expires_in,
                session=session,
            )
