import logging
import os
import boto3
from response_utils import ErrorCode, build_success_response, build_error_response

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")

CONTENT_TYPE_MAPPING = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".flv": "video/x-flv",
    ".wmv": "video/x-ms-wmv",
    ".mpeg": "video/mpeg",
    ".mpg": "video/mpeg",
    ".mpe": "video/mpeg",
    ".m4v": "video/x-m4v",
    ".3gp": "video/3gpp",
    ".ogv": "video/ogg",
    ".ts": "video/mp2t",
    ".mxf": "application/mxf",
}


def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()


def is_valid_file_extension(file_extension):
    return file_extension in CONTENT_TYPE_MAPPING


def get_content_type(file_extension):
    return CONTENT_TYPE_MAPPING.get(file_extension, "application/octet-stream")


def lambda_handler(event, context):
    try:
        query_params = event.get("queryStringParameters")
        if not query_params:
            logger.error("Missing queryStringParameters")
            return build_error_response(
                status_code=400,
                message="Missing query parameters",
                error_code=ErrorCode.INVALID_REQUEST,
            )
        
        filename = query_params.get("filename")
        if not filename:
            logger.error("Missing filename parameter")
            return build_error_response(
                status_code=400,
                message="Missing required parameter: filename",
                error_code=ErrorCode.INVALID_REQUEST,
            )

        logger.info(f"Processing filename: {filename}")

        file_extension = get_file_extension(filename)
        if not is_valid_file_extension(file_extension):
            valid_extensions = "\n".join(sorted(list(CONTENT_TYPE_MAPPING.keys())))
            message = f"Invalid video file extension: {file_extension}.\nValid extensions: {valid_extensions},"
            logger.warning(message)
            return build_error_response(status_code=400, message=message)

        bucket_name = os.environ.get("S3_BUCKET_NAME")
        object_key = filename
        expiration = int(os.environ.get("PRESIGNED_URL_EXPIRATION", 3600))

        logger.info(
            f"Generating presigned URL for bucket: {bucket_name}, key: {object_key}"
        )

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket_name,
                "Key": object_key,
                "ContentType": get_content_type(file_extension),
            },
            ExpiresIn=expiration,
        )

        logger.info("Presigned URL generated successfully")

        return build_success_response(
            data={
                "presigned_url": presigned_url,
                "filename": filename,
                "file_extension": file_extension,
                "bucket_name": bucket_name,
                "object_key": object_key,
                "expires_in_seconds": expiration,
                "upload_method": "PUT",
                "content_type": get_content_type(file_extension),
            },
        )

    except Exception as e:
        logger.exception("Unexpected error:", e)

        return build_error_response(
            status_code=500,
            message="Internal server error: An unexpected error occurred while generating the upload URL",
            error_code=ErrorCode.INTERNAL_ERROR,
        )
