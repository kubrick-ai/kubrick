import os
import asyncio
import aioboto3
import boto3
from botocore.config import Config
import logging

S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_CLIENT_CONFIG = (
    Config(
        region_name=S3_REGION,
        signature_version="s3v4",
        s3={"addressing_style": "virtual"},
    ),
)
logger = logging.getLogger()


def generate_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    s3 = boto3.client("s3", region_name=S3_REGION, config=S3_CLIENT_CONFIG)
    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        raise


async def generate_presigned_url_async(
    bucket: str,
    key: str,
    expires_in: int = 3600,
    s3_client=aioboto3.Session().client(
        "s3", region_name=S3_REGION, config=S3_CLIENT_CONFIG
    ),
) -> str:
    try:
        url = await s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
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
    async with session.client(
        "s3", region_name=S3_REGION, config=S3_CLIENT_CONFIG
    ) as s3_client:  # type: ignore (type error in aioboto3 library)
        for item in items:
            if item.get("s3_bucket") and item.get("s3_key"):
                item["url"] = await generate_presigned_url_async(
                    item["s3_bucket"], item["s3_key"], expires_in, s3_client
                )
