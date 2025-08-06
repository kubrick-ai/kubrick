import os
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
    for k, v in kwargs.items():
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
