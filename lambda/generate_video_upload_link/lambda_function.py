import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

VALID_VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
    ".mpeg",
    ".mpg",
    ".mpe",
    ".m4v",
    ".3gp",
    ".ogv",
    ".ts",
    ".mxf",
}


def get_content_type(file_extension):
    content_type_mapping = {
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

    return content_type_mapping.get(file_extension, "application/octet-stream")


def lambda_handler(event, context):
    try:
        filename = event["queryStringParameters"]["filename"]
        if not filename:
            logger.error("Missing filename parameter")
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": {
                    "success": False,
                    "error": "Missing required parameter: filename",
                    "message": "Please provide a filename in the request",
                },
            }

        logger.info(f"Processing filename: {filename}")

        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension not in VALID_VIDEO_EXTENSIONS:
            logger.warning(f"Invalid video extension: {file_extension}")
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": {
                    "success": False,
                    "error": f"Invalid video file extension: {file_extension}",
                    "valid_extensions": sorted(list(VALID_VIDEO_EXTENSIONS)),
                    "message": "Please provide a valid video file",
                },
            }

        bucket_name = os.environ.get("S3_BUCKET_NAME")
        object_key = filename
        expiration = int(os.environ.get("PRESIGNED_URL_EXPIRATION"))

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

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "success": True,
                    "data": {
                        "presigned_url": presigned_url,
                        "filename": filename,
                        "file_extension": file_extension,
                        "bucket_name": bucket_name,
                        "object_key": object_key,
                        "expires_in_seconds": expiration,
                        "upload_method": "PUT",
                        "content_type": get_content_type(file_extension),
                    },
                    "message": "Upload URL generated successfully",
                }
            ),
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": {
                "success": False,
                "error": "Internal server error",
                "message": "An unexpected error occurred while generating the upload URL",
            },
        }
