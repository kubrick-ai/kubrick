import boto3
import logging
import json
from enum import Enum
from typing import Dict, Any, Union, List, TypedDict

# API Gateway should be set up with Lambda proxy


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


def build_options_response() -> LambdaProxyResponse:
    """Build a CORS preflight OPTIONS response."""
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps({}),
    }


def build_cors_headers() -> Dict[str, str]:
    """Build standard CORS headers for Lambda responses."""
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
    }


def build_success_response(
    data: Union[List[Any], Dict[str, Any], Any],
) -> LambdaProxyResponse:
    """Build a successful Lambda response with data."""
    return {
        "statusCode": 200,
        "headers": build_cors_headers(),
        "body": json.dumps({"data": data}),
    }


def build_error_response(
    status_code: int, message: str, error_code: ErrorCode = ErrorCode.INTERNAL_ERROR
) -> LambdaProxyResponse:
    """Build an error Lambda response with status code and message."""
    return {
        "statusCode": status_code,
        "headers": build_cors_headers(),
        "body": json.dumps({"error": {"code": error_code.value, "message": message}}),
    }


def generate_presigned_url(
    bucket: str, key: str, expires_in: int = 3600, logger=logging.getLogger()
) -> str:
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
