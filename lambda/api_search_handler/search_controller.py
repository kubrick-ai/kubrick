import json
import base64
import multipart
import io
from embed_service import EmbedService
from vector_db_service import VectorDBService
from logging import getLogger, Logger
from typing import Dict, List, Any, Optional, Union, Literal
from response_utils import add_presigned_urls
from search_errors import (
    SearchError,
    SearchRequestError,
    EmbeddingError,
    DatabaseError,
    MediaProcessingError,
)
from pydantic import BaseModel, Field, field_validator, ValidationError

DEFAULT_PAGE_LIMIT = 10
DEFAULT_QUERY_MODALITY: List[Literal["visual-text", "audio"]] = ["visual-text"]
DEFAULT_MIN_SIMILARITY = 0.2


class SearchRequest(BaseModel):
    query_type: Literal["text", "image", "video", "audio"] = "text"
    query_text: Optional[str] = None
    page_limit: int = Field(DEFAULT_PAGE_LIMIT, gt=0, description="Must be positive")
    min_similarity: Optional[float] = Field(
        DEFAULT_MIN_SIMILARITY, ge=0, le=1, description="Must be between 0 and 1"
    )
    query_media_file: Optional[bytes] = None
    query_media_url: Optional[str] = None
    query_modality: List[Literal["visual-text", "audio"]] = DEFAULT_QUERY_MODALITY
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

    def get_search_params(self) -> Dict[str, Any]:
        """Extract search parameters for vector database"""
        return {
            "filter": self.filter,
            "page_limit": self.page_limit,
            "min_similarity": self.min_similarity,
        }

    def get_query_media_file_bytestream(self):
        if not self.query_media_file:
            raise ValueError("Cannot get bytestream for query_media_file: None")
        return io.BytesIO(self.query_media_file)


class SearchController:
    def __init__(
        self,
        embed_service: EmbedService,
        vector_db_service: VectorDBService,
        query_media_file_size_limit: int = 6000000,
        logger: Logger = getLogger(),
    ):
        self.embed_service = embed_service
        self.vector_db_service = vector_db_service
        self.query_media_file_size_limit = query_media_file_size_limit
        self.logger = logger

    def parse_lambda_event(self, event) -> SearchRequest:
        # Lambda event body must be passed as binary data
        try:
            self.logger.info("Starting multipart parsing")

            if not event.get("body"):
                raise SearchRequestError("Request body is empty")

            try:
                byte_string = base64.b64decode(event.get("body"))
                self.logger.debug(f"Decoded body length: {len(byte_string)}")
            except Exception as e:
                raise SearchRequestError(f"Failed to decode base64 body: {str(e)}")

            headers = event.get("headers", {})
            normalized_headers = {k.lower(): v for k, v in headers.items()}
            content_type_header = normalized_headers.get("content-type")

            if not content_type_header:
                raise SearchRequestError("Missing content-type header")

            try:
                content_type, options = multipart.parse_options_header(
                    content_type_header
                )

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

            # Get valid field names from the SearchFormData model
            valid_fields = set(SearchRequest.model_fields.keys())
            search_request: Dict[str, Any] = {}

            # Extract form fields
            try:
                for part in parsed:
                    if not part or (field_name := part.name) not in valid_fields:
                        continue

                    if part.filename:  # File field
                        file_size = part.size
                        size_limit = self.query_media_file_size_limit
                        if file_size > size_limit:
                            raise SearchRequestError(
                                f"Query media file size too large. Limit: {size_limit/1000} KB"
                            )
                        search_request[field_name] = part.raw
                        self.logger.debug(
                            f"Processed file field: {field_name}, size: {file_size/1000} KB"
                        )
                    else:  # Text field
                        try:
                            value = part.value
                            if field_name in ["filter", "query_modality"] and value:
                                value = json.loads(value)
                            search_request[field_name] = value
                            self.logger.debug(f"Processed text field: {field_name}")
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
                validated_request = SearchRequest(**search_request)
                self.logger.info("Search request validation passed")
                return validated_request
            except ValidationError as e:
                error_details = {
                    "validation_errors": [
                        {"field": err["loc"], "message": err["msg"]}
                        for err in e.errors()
                    ]
                }
                self.logger.error(
                    f"Request validation failed: {str(e)}: {error_details}"
                )
                raise SearchRequestError(
                    f"Request validation failed: {str(e)}",
                )

        except SearchRequestError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in parse_form_data: {str(e)}")
            raise SearchRequestError(f"Failed to parse request: {str(e)}")

    def process_search_request(self, event) -> tuple[List[Any], dict[str, int]]:
        """Parse event to SearchRequest and execute the search request"""
        try:
            self.logger.info("Processing search request")
            search_request = self.parse_lambda_event(event)
            query_type = search_request.query_type

            match query_type:
                case "text":
                    results = self.text_search(search_request=search_request)
                case "image" | "audio" | "video":
                    results = self.media_search(
                        search_request=search_request, media_type=query_type
                    )
                case _:
                    raise SearchRequestError(f"Unsupported query_type: {query_type}")

            # Add presigned url to each result
            try:
                add_presigned_urls(result["video"] for result in results)
                self.logger.info(
                    f"Successfully processed search request, returning {len(results)} results"
                )
                metadata = {
                    "page": 0,
                    "limit": search_request.page_limit,
                    "total": len(results),
                }
                return results, metadata
            except Exception as e:
                self.logger.exception(f"Error adding URLs to results: {str(e)}")
                raise SearchError(f"Failed to process search results: {str(e)}")

        except SearchError:
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error processing search request: {str(e)}"
            )
            raise SearchError(f"Search request processing failed: {str(e)}")

    def _perform_vector_search(
        self,
        embedding: Union[List[float], List[List[float]]],
        search_params: Dict[str, Any],
        use_batch: bool = False,
    ) -> List[Any]:
        """Perform vector database search with given embedding(s)"""
        try:
            self.logger.debug(
                f"Performing {'batch' if use_batch else 'single'} vector search"
            )

            if use_batch:
                if not isinstance(embedding, list) or not all(
                    isinstance(emb, list) for emb in embedding
                ):
                    raise DatabaseError("Batch search requires list of embeddings")
                results = self.vector_db_service.find_similar_batch(
                    embeddings=embedding, **search_params
                )
            else:
                if not isinstance(embedding, list) or any(
                    isinstance(item, list) for item in embedding
                ):
                    raise DatabaseError("Single search requires flat embedding list")
                results = self.vector_db_service.find_similar(
                    embedding=embedding, **search_params
                )

            if results is None:
                self.logger.warning(
                    "Vector search returned None, treating as empty results"
                )
                return []

            self.logger.debug(f"Vector search returned {len(results)} results")
            return results

        except DatabaseError:
            raise
        except Exception as e:
            details = {
                "search_type": "batch" if use_batch else "single",
                "embedding_count": len(embedding) if use_batch else 1,
                "search_params": search_params,
            }
            self.logger.exception(
                f"Unexpected error during vector search: {str(e)}\n{details}"
            )
            raise DatabaseError(f"Vector database search failed: {str(e)}")

    def _extract_text_embedding(self, query_text: str) -> List[float]:
        """Extract text embedding with error handling"""
        try:
            self.logger.info(
                f"Extracting text embedding for query (length: {len(query_text)})"
            )
            embedding = self.embed_service.extract_text_embedding(query_text)

            if not embedding:
                raise EmbeddingError("Text embedding extraction returned empty result")
            if not isinstance(embedding, list):
                raise EmbeddingError(
                    "Text embedding extraction returned invalid format"
                )

            self.logger.debug(
                f"Successfully extracted text embedding with {len(embedding)} dimensions"
            )
            return embedding
        except EmbeddingError:
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error during text embedding extraction: {str(e)}"
            )
            raise EmbeddingError(f"Failed to extract text embedding: {str(e)}")

    def _extract_media_embedding(
        self,
        search_request: SearchRequest,
        media_type: Literal["image", "audio", "video"],
    ) -> Union[List[float], List[List[float]]]:
        """Extract embedding from either file or URL"""
        try:
            media_url = search_request.query_media_url
            media_file = search_request.get_query_media_file_bytestream()
            query_modality = getattr(search_request, "query_modality", None)

            extract_fn = {
                "image": self.embed_service.extract_image_embedding,
                "audio": self.embed_service.extract_audio_embedding,
                "video": self.embed_service.extract_video_embedding,
            }.get(media_type)

            if not extract_fn:
                raise MediaProcessingError(f"Unsupported media type: {media_type}")

            if media_url:
                self.logger.info(
                    f"Extracting {media_type} embedding from URL"
                    + (
                        f" with modality: {query_modality}"
                        if media_type == "video"
                        else ""
                    )
                )
                self.logger.debug(f"{media_type.title()} URL: {media_url}")
                if media_type == "video":
                    embeddings = extract_fn(
                        url=media_url, query_modality=query_modality
                    )
                else:
                    embeddings = extract_fn(url=media_url)
            elif media_file:
                self.logger.info(
                    f"Extracting {media_type} embedding from file"
                    + (
                        f" with modality: {query_modality}"
                        if media_type == "video"
                        else ""
                    )
                )
                if media_type == "video":
                    embeddings = extract_fn(
                        file=media_file, query_modality=query_modality
                    )
                else:
                    embeddings = extract_fn(file=media_file)
            else:
                self.logger.exception(
                    f"Could not extract media_url or media_file from search_request: {search_request}"
                )
                raise MediaProcessingError(
                    f"Missing media input for {media_type} embedding extraction"
                )

            if not embeddings:
                raise EmbeddingError(
                    f"{media_type.title()} embedding extraction returned empty result"
                )

            # Validate format
            if media_type == "video":
                if not isinstance(embeddings, list) or not all(
                    isinstance(emb, list) for emb in embeddings
                ):
                    raise EmbeddingError("Video embedding must be list of lists")
            else:
                if not isinstance(embeddings, list) or any(
                    isinstance(emb, list) for emb in embeddings
                ):
                    raise EmbeddingError(
                        f"{media_type.title()} embedding format is invalid"
                    )

            return embeddings

        except (EmbeddingError, MediaProcessingError):
            raise
        except Exception as e:
            self.logger.exception(f"Error extracting {media_type} embedding: {str(e)}")
            raise EmbeddingError(f"{media_type.title()} embedding failed: {str(e)}")

    def text_search(self, search_request: SearchRequest) -> List[Any]:
        try:
            self.logger.info("Starting text search")

            if not search_request.query_text:
                raise SearchRequestError("query_text is required for text search")
            embedding = self._extract_text_embedding(search_request.query_text)
            search_params = search_request.get_search_params()
            results = self._perform_vector_search(embedding, search_params)

            self.logger.info(f"Text search completed, found {len(results)} results")
            return results

        except (SearchRequestError, EmbeddingError, DatabaseError):
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error in text search: {str(e)}")
            raise SearchError(f"Text search failed: {str(e)}")

    def media_search(
        self,
        search_request: SearchRequest,
        media_type: Literal["image", "audio", "video"],
    ) -> List[Any]:
        try:
            self.logger.info(f"Starting {media_type} search")
            embedding = self._extract_media_embedding(search_request, media_type)
            search_params = search_request.get_search_params()
            use_batch = False

            if media_type == "video":
                if isinstance(embedding, list) and isinstance(embedding[0], list):
                    if len(embedding) > 1:
                        use_batch = True
                        self.logger.debug("Using batch search for multiple embeddings")
                    else:
                        embedding = embedding[0]
                else:
                    self.logger.debug("Using single search for one embedding")

            results = self._perform_vector_search(
                embedding, search_params, use_batch=use_batch
            )
            self.logger.info(
                f"{media_type.title()} search completed, found {len(results)} results"
            )
            return results

        except (
            SearchRequestError,
            EmbeddingError,
            MediaProcessingError,
            DatabaseError,
        ):
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error in {media_type} search: {str(e)}")
            raise SearchError(f"{media_type.title()} search failed: {str(e)}")
