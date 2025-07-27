import os
import json
import base64
import multipart
import io
from embed_service import EmbedService
from vector_db_service import VectorDBService
from search_controller import SearchController
from search_errors import (
    SearchError,
    SearchRequestError,
    EmbeddingError,
    MediaProcessingError,
    DatabaseError,
)
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Optional, Literal, List, Dict, Any
from config import load_config, get_secret, setup_logging, get_db_config
from response_utils import (
    build_success_response,
    build_error_response,
    build_options_response,
    ErrorCode,
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


def parse_form_data(event, logger) -> SearchFormData:
    try:
        logger.info("Starting multipart parsing")

        if not event.get("body"):
            raise SearchRequestError("Request body is empty")

        try:
            byte_string = base64.b64decode(event.get("body"))
            logger.debug(f"Decoded body length: {len(byte_string)}")
        except Exception as e:
            raise SearchRequestError(f"Failed to decode base64 body: {str(e)}")

        headers = event.get("headers", {})
        content_type_header = headers.get("content-type")

        if not content_type_header:
            raise SearchRequestError("Missing content-type header")

        try:
            content_type, options = multipart.parse_options_header(content_type_header)

            if content_type != "multipart/form-data":
                raise SearchRequestError(
                    f"Expected content-type 'multipart/form-data', got '{content_type}'"
                )

            boundary = options.get("boundary")
            if not boundary:
                raise SearchRequestError("Missing boundary in content-type header")

        except SearchRequestError:
            raise
        except Exception as e:
            raise SearchRequestError(f"Invalid content-type header: {str(e)}")

        try:
            body_stream = io.BytesIO(byte_string)
            parsed = multipart.MultipartParser(body_stream, boundary)
        except Exception as e:
            raise SearchRequestError(f"Failed to parse multipart data: {str(e)}")

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

        # Extract form fields
        try:
            for part in parsed:
                if not part or not part.name:
                    continue

                field_name = part.name
                if field_name in search_request:
                    if part.filename:  # File field
                        search_request[field_name] = part.raw
                        logger.debug(
                            f"Processed file field: {field_name}, size: {len(part.raw) if part.raw else 0}"
                        )
                    else:  # Text field
                        try:
                            value = (
                                part.value
                                if isinstance(part.value, str)
                                else part.value.decode("utf-8")
                            )
                            if field_name == "filter" and value:
                                value = json.loads(value)
                            search_request[field_name] = value
                            logger.debug(f"Processed text field: {field_name}")
                        except json.JSONDecodeError as e:
                            raise SearchRequestError(
                                f"Invalid JSON in filter field: {str(e)}"
                            )
                        except UnicodeDecodeError as e:
                            raise SearchRequestError(
                                f"Invalid encoding in field {field_name}: {str(e)}"
                            )

            # Cleanup
            for part in parsed.parts():
                if part:
                    part.close()

        except SearchRequestError:
            raise
        except Exception as e:
            raise SearchRequestError(f"Error processing form fields: {str(e)}")

        # Validate with Pydantic
        try:
            validated_request = SearchFormData(**search_request)
            logger.info("Search request validation passed")
            return validated_request
        except ValidationError as e:
            error_details = {
                "validation_errors": [
                    {"field": err["loc"], "message": err["msg"]} for err in e.errors()
                ]
            }
            raise SearchRequestError(
                f"Request validation failed: {str(e)}", error_details
            )

    except SearchRequestError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in parse_form_data: {str(e)}")
        raise SearchRequestError(f"Failed to parse request: {str(e)}")


def lambda_handler(event, context):
    logger = setup_logging()
    config = load_config()
    SECRET = get_secret(config)
    DB_CONFIG = get_db_config(SECRET)

    # Handle preflight request (CORS)
    if event.get("httpMethod") == "OPTIONS":
        return build_options_response(allowed_methods=["POST", "OPTIONS"])

    logger.debug(f"event={event}")

    # Initialize services
    embed_service = EmbedService(
        api_key=SECRET["TWELVELABS_API_KEY"],
        model_name=os.getenv("EMBEDDING_MODEL_NAME", "Marengo-retrieval-2.7"),
        clip_length=int(os.getenv("DEFAULT_CLIP_LENGTH", 6)),
        logger=logger,
    )
    vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)
    search_controller = SearchController(
        embed_service=embed_service, vector_db_service=vector_db_service, logger=logger
    )

    try:
        # Parse form data from Lambda event
        search_request = parse_form_data(event, logger)
        search_request_dict = search_request.model_dump()

        # Process search request
        results = search_controller.process_search_request(search_request_dict)
        return build_success_response(results)

    except SearchRequestError as e:
        logger.error(f"Search request error: {e}")
        return build_error_response(400, str(e), e.error_code, details=e.details)
    except EmbeddingError as e:
        logger.error(f"Embedding error: {e}")
        return build_error_response(422, str(e), e.error_code, details=e.details)
    except MediaProcessingError as e:
        logger.error(f"Media processing error: {e}")
        return build_error_response(422, str(e), e.error_code, details=e.details)
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return build_error_response(
            503,
            "Search service temporarily unavailable",
            e.error_code,
            details=e.details,
        )
    except SearchError as e:
        logger.error(f"Search error: {e}")
        return build_error_response(500, str(e), e.error_code, details=e.details)
    except ValidationError as e:
        logger.error(f"Pydantic validation error: {e}")
        return build_error_response(
            400, f"Invalid request format: {e}", ErrorCode.VALIDATION_ERROR
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return build_error_response(
            500, "Internal server error", ErrorCode.INTERNAL_ERROR
        )
