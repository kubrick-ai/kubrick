import os
import asyncio
import aioboto3
import boto3
import logging
import json
from enum import Enum
from typing import Dict, Any, Union, List, TypedDict


CORS_ALLOWED_ORIGIN = os.getenv("CORS_ALLOWED_ORIGIN", "*")
logger = logging.getLogger()


# Note: AWS API Gateway should be set up with Lambda proxy for this response type to be returned properly
class LambdaProxyResponse(TypedDict):
    """Type definition for AWS Lambda proxy integration response."""

    statusCode: int
    headers: Dict[str, str]
    body: str


class ErrorCode(Enum):
    """Standard error codes for API responses."""

    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_BOUNDARY = "MISSING_BOUNDARY"
    UNSUPPORTED_QUERY_TYPE = "UNSUPPORTED_QUERY_TYPE"
    PARSING_ERROR = "PARSING_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EMBEDDING_ERROR = "EMBEDDING_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    MEDIA_PROCESSING_ERROR = "MEDIA_PROCESSING_ERROR"


def build_options_response(
    allowed_methods=["GET", "OPTIONS"],
    allowed_headers=["Content-Type", "Authorization"],
) -> LambdaProxyResponse:
    """Build a CORS preflight OPTIONS response."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": ", ".join(allowed_methods),
            "Access-Control-Allow-Headers": ", ".join(allowed_headers),
        },
        "body": "",
    }


def build_cors_headers(allowed_origin=CORS_ALLOWED_ORIGIN, **kwargs) -> Dict[str, str]:
    """Build standard CORS headers for Lambda proxy API responses."""
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": allowed_origin,
    }
    for k, v in kwargs:
        headers[k] = v
    return headers


def build_success_response(
    data: Union[List[Any], Dict[str, Any], Any],
    metadata: Dict[str, Any] = {},
    allowed_origin=CORS_ALLOWED_ORIGIN,
) -> LambdaProxyResponse:
    """Build a successful Lambda response with data."""
    return {
        "statusCode": 200,
        "headers": build_cors_headers(allowed_origin),
        "body": json.dumps({"data": data, "metadata": metadata}),
    }


def build_error_response(
    status_code: int,
    message: str,
    error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
) -> LambdaProxyResponse:
    """Build an error Lambda response with status code and message."""
    return {
        "statusCode": status_code,
        "headers": build_cors_headers(),
        "body": json.dumps({"error": {"code": error_code.value, "message": message}}),
    }


def generate_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    s3 = boto3.client("s3")
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
    s3_client=aioboto3.Session().client("s3"),
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
    async with session.client("s3") as s3_client:  # type: ignore (type error in aioboto3 library)
        for item in items:
            if item.get("s3_bucket") and item.get("s3_key"):
                item["url"] = await generate_presigned_url_async(
                    item["s3_bucket"], item["s3_key"], expires_in, s3_client
                )
