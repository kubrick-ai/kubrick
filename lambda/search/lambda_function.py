import json
import logging
import os
import base64
import multipart
import io
from embed_service import EmbedService
from vector_db_service import VectorDBService
from search_service import SearchService
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ValidationError
from config import load_config, get_secret, setup_logging, get_db_config
from response_utils import (
    build_success_response,
    build_error_response,
    build_options_response,
    ErrorCode,
    generate_presigned_url,
)


class SearchFormData(BaseModel):
    query_type: Literal["text", "image", "video", "audio"] = "text"
    query_text: Optional[str] = None
    page_limit: Optional[int] = Field(None, gt=0, description="Must be positive")
    min_similarity: Optional[float] = Field(
        None, ge=0, le=1, description="Must be between 0 and 1"
    )
    query_media_file: Optional[bytes] = None
    query_media_url: Optional[str] = None
    query_modality: List[Literal["visual-text", "audio"]] = ["visual-text"]
    filter: Optional[dict[str, Any]] = None

    @field_validator("query_text")
    @classmethod
    def validate_text_query(cls, value, info):
        query_type = info.data.get("query_type")
        if query_type == "text" and not value:
            raise ValueError("query_text is required for text search")
        return value

    @field_validator("query_media_url")
    @classmethod
    def validate_media_query(cls, value, info):
        query_type = info.data.get("query_type")
        if query_type in ["image", "video", "audio"]:
            query_media_file = info.data.get("query_media_file")
            if value is None and query_media_file is None:
                raise ValueError(
                    f"query_media_url or query_media_file required for {query_type} search"
                )
        return value


def parse_form_data(event, logger=logging.getLogger()) -> SearchFormData:
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

    # Initialize search request as dict for parsing
    search_request: Dict[str, Any] = {
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

    # Validate with Pydantic
    try:
        validated_request = SearchFormData(**search_request)
        logger.info("Search request validation passed")
        return validated_request
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise ValueError(f"Invalid request: {e}")


def add_url(result):
    result["video"]["url"] = generate_presigned_url(
        bucket=result["video"]["s3_bucket"], key=result["video"]["s3_key"]
    )
    return result


def lambda_handler(event, context):
    logger = setup_logging()
    config = load_config()
    SECRET = get_secret(config)
    DB_CONFIG = get_db_config(SECRET)

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
        return build_options_response(allowed_methods=["POST", "OPTIONS"])

    logger.debug(f"event={event}")

    try:
        search_request = parse_form_data(event)
        # Convert Pydantic model to dict for search services
        search_request_dict = search_request.model_dump()

        match query_type := search_request.query_type:
            case "text":
                results = search_service.text_search(search_request=search_request_dict)
            case "image":
                results = search_service.image_search(
                    search_request=search_request_dict
                )
            case "video":
                results = search_service.video_search(
                    search_request=search_request_dict
                )
            # TODO: case "audio"
            case _:
                return build_error_response(
                    400,
                    f"Unsupported query_type: {query_type}",
                    ErrorCode.UNSUPPORTED_QUERY_TYPE,
                )

    except ValidationError as e:
        logger.error(f"Pydantic validation error: {e}")
        return build_error_response(
            400, f"Invalid request: {e}", ErrorCode.VALIDATION_ERROR
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
