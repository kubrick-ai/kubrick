import json
import logging
import os
import boto3
import base64
import multipart
import io
from embed_service import EmbedService
from vector_db_service import VectorDBService
from search_service import SearchService
from typing import TypedDict, Optional, Literal


class SearchFormData(TypedDict):
    query_text: Optional[str]
    page_limit: Optional[int]
    min_similarity: Optional[float]
    query_type: Optional[Literal["text", "image", "video", "audio"]]
    query_media_url: Optional[str]
    query_media_file: Optional[bytes]
    query_modality: Optional[list[Literal["visual-text", "audio"]]]
    filter: Optional[str]


logger = logging.getLogger()
logger.setLevel(logging.INFO)
secretsmanager = boto3.client("secretsmanager")


with open("config.json") as f:
    CONFIG = json.load(f)

try:
    sm_response = secretsmanager.get_secret_value(SecretId=CONFIG["secret_name"])
    SECRETS = json.loads(sm_response["SecretString"])
except Exception as e:
    logger.error(f"Failed to retrieve secret: {e}")
    raise

API_KEY = SECRETS["TWELVELABS_API_KEY"]

DB_CONFIG = {
    "host": os.getenv("DB_URL"),
    "database": "kubrick",
    "user": "postgres",
    "password": SECRETS["DB_PASSWORD"],
    "port": 5432,
}

embed_service = EmbedService(
    api_key=API_KEY,
    model_name=os.getenv("EMBEDDING_MODEL_NAME", "Marengo-retrieval-2.7"),
    clip_length=int(os.getenv("DEFAULT_CLIP_LENGTH", 6)),
)

vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)

search_service = SearchService(
    embed_service=embed_service, vector_db_service=vector_db_service, logger=logger
)


def lambda_handler(event, context):
    # Handle preflight request (CORS)
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "GET,OPTIONS",
            },
            "body": json.dumps({}),
        }

    logger.info(f"event={event}")

    try:
        logger.info("Starting multipart parsing...")
        # Decode base64 body
        logger.info("Decoding base64 body...")
        body_data = base64.b64decode(event["body"])
        logger.info(f"Decoded body length: {len(body_data)}")

        # Extract boundary from content-type header
        logger.info("Extracting boundary...")
        content_type = event.get("content-type", "")
        logger.info(f"Content-type: {content_type}")
        boundary = (
            content_type.split("boundary=")[1] if "boundary=" in content_type else None
        )
        logger.info(f"Extracted boundary: {boundary}")

        if not boundary:
            logger.error("No boundary found in content-type header")
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                "body": {
                    "success": False,
                    "message": "Missing boundary in content-type header",
                },
            }

        # Parse multipart data
        logger.info("Creating BytesIO stream...")
        body_stream = io.BytesIO(body_data)
        logger.info("Creating multipart parser...")
        parsed = multipart.MultipartParser(body_stream, boundary.encode())
        logger.info("Parser created successfully")

        # Extract form fields
        logger.info("Initializing search_request dictionary...")

        # Initialize with None
        search_request: SearchFormData = {
            "query_text": None,
            "page_limit": None,
            "min_similarity": None,
            "query_type": None,
            "query_media_url": None,
            "query_media_file": None,
            "query_modality": None,
            "filter": None,
        }

        logger.info("Starting to iterate through parser parts...")
        for part in parsed:
            if not part:
                continue
            logger.info(f"Processing part: {part.name}")
            field_name = part.name
            if field_name in search_request:
                if part.filename:  # File field
                    logger.info(f"Processing file field: {field_name}")
                    search_request[field_name] = part.raw
                else:  # Text field
                    logger.info(f"Processing text field: {field_name}")
                    value = (
                        part.value
                        if isinstance(part.value, str)
                        else part.value.decode("utf-8")
                    )
                    if field_name == "filter":
                        value = json.loads(value)
                    search_request[field_name] = value

        logger.info("Finished processing all parts")
        logger.info(f"Parsed formdata: {search_request}")

        if search_request["query_type"] == "text":
            results = search_service.text_search(search_request=search_request)

        elif search_request["query_type"] == "image":
            results = search_service.image_search(search_request=search_request)

        elif search_request["query_type"] == "video":
            results = search_service.video_search(search_request=search_request)

        else:
            raise Exception(f"Unsupported query_type: {search_request['query_type']}")

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": {
                "success": False,
                "message": f"Error processing request: {str(e)}",
            },
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "data": [add_url(result) for result in results],
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


def add_url(result):
    result["video"]["url"] = generate_presigned_url(
        result["video"]["s3_bucket"], result["video"]["s3_key"]
    )
    return result
