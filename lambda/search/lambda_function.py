import json
from logging import getLogger, INFO
import os
import boto3
import base64
import multipart
import io
from embed_service import EmbedService
from vector_db_service import VectorDBService
from search_service import SearchService
from typing import TypedDict, Optional, Literal
from config import load_config, get_secret
from response_utils import (
    build_success_response,
    build_error_response,
    build_options_response,
    ErrorCode,
)


class SearchFormData(TypedDict):
    query_text: Optional[str]
    page_limit: Optional[int]
    min_similarity: Optional[float]
    query_type: Optional[Literal["text", "image", "video", "audio"]]
    query_media_url: Optional[str]
    query_media_file: Optional[bytes]
    query_modality: Optional[list[Literal["visual-text", "audio"]]]
    filter: Optional[str]


def parse_form_data(event, logger=getLogger(__name__)):
    logger.info("Starting multipart parsing...")
    # Decode base64 body
    logger.info("Decoding base64 body...")
    body_data = base64.b64decode(event.get("body"))
    logger.info(f"Decoded body length: {len(body_data)}")

    headers = event.get("headers")

    # Extract boundary from content-type header
    logger.info("Extracting boundary...")
    content_type, options = multipart.parse_options_header(headers.get("content-type"))
    logger.info(f"Content-type: {content_type}")
    logger.info(f"Options: {options}")
    boundary = options.get("boundary")
    logger.info(f"Boundary: {boundary}")

    if not boundary:
        logger.error("No boundary found in content-type header")
        raise ValueError("Missing boundary in content-type header")

    # Parse multipart data
    logger.info("Creating BytesIO stream...")
    body_stream = io.BytesIO(body_data)
    logger.info("Creating multipart parser...")
    parsed = multipart.MultipartParser(body_stream, boundary)
    logger.info("Parser created successfully")

    # Extract form fields
    logger.info("Initializing search_request dictionary...")

    # Initialize search request
    search_request: SearchFormData = {
        "query_text": None,
        "page_limit": None,
        "min_similarity": None,
        "query_type": None,
        "query_media_url": None,
        "query_media_file": None,
        "query_modality": ["visual-text"],
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

    # clean up
    for part in parsed.parts():
        if part:
            part.close()

    logger.info("Finished processing all parts")
    logger.info(f"Parsed formdata: {search_request}")

    return search_request


def generate_presigned_url(
    bucket: str, key: str, expires_in: int = 3600, logger=getLogger(__name__)
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


def add_url(result):
    result["video"]["url"] = generate_presigned_url(
        result["video"]["s3_bucket"], result["video"]["s3_key"]
    )
    return result


def lambda_handler(event, context):
    logger = getLogger()
    # TODO: Don't hard code logging level
    logger.setLevel(INFO)

    config = load_config()
    SECRET = get_secret(config)

    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "kubrick"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": SECRET["DB_PASSWORD"],
        "port": int(os.getenv("DB_PORT", 5432)),
    }

    embed_service = EmbedService(
        api_key=SECRET["TWELVELABS_API_KEY"],
        model_name=os.getenv("EMBEDDING_MODEL_NAME", "Marengo-retrieval-2.7"),
        clip_length=int(os.getenv("DEFAULT_CLIP_LENGTH", 6)),
        logger=logger,
    )

    vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)

    search_service = SearchService(
        embed_service=embed_service, vector_db_service=vector_db_service, logger=logger
    )

    # Handle preflight request (CORS)
    if event.get("httpMethod") == "OPTIONS":
        return build_options_response()

    logger.info(f"event={event}")

    try:
        search_request = parse_form_data(event)
        match query_type := search_request["query_type"]:
            case "text":
                results = search_service.text_search(search_request=search_request)
            case "image":
                results = search_service.image_search(search_request=search_request)
            case "video":
                results = search_service.video_search(search_request=search_request)
            # TODO: case "audio"
            case _:
                return build_error_response(
                    400,
                    f"Unsupported query_type: {query_type}",
                    ErrorCode.UNSUPPORTED_QUERY_TYPE,
                )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response(400, str(e), ErrorCode.VALIDATION_ERROR)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return build_error_response(
            500, f"Error processing request: {e}", ErrorCode.INTERNAL_ERROR
        )

    return build_success_response([add_url(result) for result in results])
