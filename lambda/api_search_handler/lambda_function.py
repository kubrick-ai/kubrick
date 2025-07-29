import os
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
from pydantic import ValidationError
from config import load_config, get_secret, setup_logging, get_db_config
from response_utils import (
    build_success_response,
    build_error_response,
    build_options_response,
    ErrorCode,
)


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
        embed_service=embed_service,
        vector_db_service=vector_db_service,
        config=config,
        logger=logger,
    )

    try:
        results, metadata = search_controller.process_search_request(event)
        return build_success_response(data=results, metadata=metadata)

    except SearchRequestError as e:
        logger.error(f"Search request error: {e}")
        return build_error_response(400, str(e), e.error_code)
    except EmbeddingError as e:
        logger.exception(f"Embedding error: {e}")
        return build_error_response(422, str(e), e.error_code)
    except MediaProcessingError as e:
        logger.exception(f"Media processing error: {e}")
        return build_error_response(422, str(e), e.error_code)
    except DatabaseError as e:
        logger.exception(f"Database error: {e}")
        return build_error_response(
            503, "Search service temporarily unavailable", e.error_code
        )
    except SearchError as e:
        logger.exception(f"Search error: {e}")
        return build_error_response(500, str(e), e.error_code)
    except ValidationError as e:
        logger.error(f"Pydantic validation error: {e}")
        return build_error_response(
            400, f"Invalid request format: {e}", ErrorCode.VALIDATION_ERROR
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return build_error_response(
            500, "Internal server error", ErrorCode.INTERNAL_ERROR
        )
