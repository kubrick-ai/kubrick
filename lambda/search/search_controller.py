import json
import base64
import multipart
import io
from embed_service import EmbedService
from vector_db_service import VectorDBService
from logging import getLogger, Logger
from typing import Dict, List, Any, Optional, Union, Literal
from response_utils import generate_presigned_url
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
    page_limit: Optional[int] = Field(
        DEFAULT_PAGE_LIMIT, gt=0, description="Must be positive"
    )
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
        config: Dict[str, Any],
        logger: Logger = getLogger(),
    ):
        self.embed_service = embed_service
        self.vector_db_service = vector_db_service
        self.config = config
        self.logger = logger

    def parse_lambda_event(self, event) -> SearchRequest:
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
            content_type_header = headers.get("content-type")

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
                        size_limit = self.config.get(
                            "query_media_file_size_limit", 6000000
                        )
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
                            if field_name == "filter" and value:
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

    def _add_url(self, result):
        """Add presigned URL to search result"""
        result["video"]["url"] = generate_presigned_url(
            bucket=result["video"]["s3_bucket"], key=result["video"]["s3_key"]
        )
        return result

    def process_search_request(self, event) -> List[Any]:
        """Parse event to SearchRequest and execute the search request"""
        try:
            self.logger.info("Processing search request")
            search_request = self.parse_lambda_event(event)

            match search_request.query_type:
                case "text":
                    results = self.text_search(search_request=search_request)
                case "image":
                    results = self.image_search(search_request=search_request)
                case "audio":
                    results = self.audio_search(search_request=search_request)
                case "video":
                    results = self.video_search(search_request=search_request)
                case "audio":
                    # TODO: Implement audio search
                    raise SearchRequestError("Audio search is not yet supported")
                case _:
                    raise SearchRequestError(
                        f"Unsupported query_type: {search_request.query_type}"
                    )

            # Add presigned url to each result
            try:
                results_with_urls = [self._add_url(result) for result in results]
                self.logger.info(
                    f"Successfully processed search request, returning {len(results_with_urls)} results"
                )
                return results_with_urls
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

    def _extract_image_embedding(self, search_request: SearchRequest) -> List[float]:
        """Extract image embedding from URL or file"""
        try:
            media_url = search_request.query_media_url
            media_file = search_request.get_query_media_file_bytestream()

            if media_url:
                self.logger.info("Extracting image embedding from URL")
                self.logger.debug(f"Image URL: {media_url}")
                embedding = self.embed_service.extract_image_embedding(url=media_url)
            elif media_file:
                self.logger.info("Extracting image embedding from file")
                embedding = self.embed_service.extract_image_embedding(file=media_file)
            else:
                self.logger.exception(
                    f"Could not extract media_url or media_file from search_request: {search_request}"
                )
                raise MediaProcessingError(
                    "Could not extract media_url or media_file from search_request"
                )

            if not embedding:
                raise EmbeddingError("Image embedding extraction returned empty result")
            if not isinstance(embedding, list):
                raise EmbeddingError(
                    "Image embedding extraction returned invalid format"
                )

            self.logger.debug(
                f"Successfully extracted image embedding with {len(embedding)} dimensions"
            )
            return embedding

        except (EmbeddingError, MediaProcessingError):
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error during image embedding extraction: {str(e)}"
            )
            raise EmbeddingError(f"Failed to extract image embedding: {str(e)}")

    def _extract_audio_embedding(self, search_request: SearchRequest) -> List[float]:
        """Extract audio embedding from URL or file"""
        try:
            media_url = search_request.query_media_url
            media_file = search_request.get_query_media_file_bytestream()

            if media_url:
                self.logger.info("Extracting audio embedding from URL")
                self.logger.debug(f"Audio URL: {media_url}")
                embedding = self.embed_service.extract_audio_embedding(url=media_url)
            elif media_file:
                self.logger.info("Extracting audio embedding from file")
                embedding = self.embed_service.extract_audio_embedding(file=media_file)
            else:
                self.logger.exception(
                    f"Could not extract media_url or media_file from search_request: {search_request}"
                )
                raise MediaProcessingError(
                    "Could not extract media_url or media_file from search_request"
                )

            if not embedding:
                raise EmbeddingError("Audio embedding extraction returned empty result")
            if not isinstance(embedding, list):
                raise EmbeddingError(
                    "Audio embedding extraction returned invalid format"
                )

            self.logger.debug(
                f"Successfully extracted audio embedding with {len(embedding)} dimensions"
            )
            return embedding

        except (EmbeddingError, MediaProcessingError):
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error during image embedding extraction: {str(e)}"
            )
            raise EmbeddingError(f"Failed to extract image embedding: {str(e)}")

    def _extract_video_embeddings(
        self, search_request: SearchRequest
    ) -> List[List[float]]:
        """Extract video embeddings from URL or file"""
        try:
            media_url = search_request.query_media_url
            media_file = search_request.get_query_media_file_bytestream()
            query_modality = search_request.query_modality

            if media_url:
                self.logger.info(
                    f"Extracting video embedding from URL with modality: {query_modality}"
                )
                self.logger.debug(f"Video URL: {media_url}")
                embeddings = self.embed_service.extract_video_embedding(
                    url=media_url, query_modality=query_modality
                )
            elif media_file:
                self.logger.info(
                    f"Extracting video embedding from file with modality: {query_modality}"
                )
                embeddings = self.embed_service.extract_video_embedding(
                    file=media_file, query_modality=query_modality
                )
            else:
                self.logger.exception(
                    f"Could not extract media_url or media_file from search_request: {search_request}"
                )
                raise MediaProcessingError(
                    "Could not extract media_url or media_file from search_request"
                )

            if not embeddings:
                raise EmbeddingError("Video embedding extraction returned empty result")
            if not isinstance(embeddings, list):
                raise EmbeddingError(
                    "Video embedding extraction returned invalid format"
                )
            if not all(isinstance(emb, list) for emb in embeddings):
                raise EmbeddingError("Video embeddings must be a list of lists")

            self.logger.debug(
                f"Successfully extracted {len(embeddings)} video embeddings"
            )
            return embeddings

        except (EmbeddingError, MediaProcessingError):
            raise
        except Exception as e:
            self.logger.exception(
                f"Unexpected error during video embedding extraction: {str(e)}"
            )
            raise EmbeddingError(f"Failed to extract video embeddings: {str(e)}")

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

    def image_search(self, search_request: SearchRequest) -> List[Any]:
        try:
            self.logger.info("Starting image search")

            embedding = self._extract_image_embedding(search_request)
            search_params = search_request.get_search_params()
            results = self._perform_vector_search(embedding, search_params)

            self.logger.info(f"Image search completed, found {len(results)} results")
            return results

        except (
            SearchRequestError,
            EmbeddingError,
            MediaProcessingError,
            DatabaseError,
        ):
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error in image search: {str(e)}")
            raise SearchError(f"Image search failed: {str(e)}")

    def audio_search(self, search_request: SearchRequest) -> List[Any]:
        try:
            self.logger.info("Starting audio search")

            embedding = self._extract_audio_embedding(search_request)
            search_params = search_request.get_search_params()
            results = self._perform_vector_search(embedding, search_params)

            self.logger.info(f"Audio search completed, found {len(results)} results")
            return results

        except (
            SearchRequestError,
            EmbeddingError,
            MediaProcessingError,
            DatabaseError,
        ):
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error in audio search: {str(e)}")
            raise SearchError(f"Audio search failed: {str(e)}")

    def video_search(self, search_request: SearchRequest) -> List[Any]:
        try:
            self.logger.info("Starting video search")

            embeddings = self._extract_video_embeddings(search_request)

            if not embeddings:
                raise EmbeddingError("Could not extract video embeddings")

            search_params = search_request.get_search_params()

            if len(embeddings) > 1:
                self.logger.debug("Using batch search for multiple embeddings")
                results = self._perform_vector_search(
                    embeddings, search_params, use_batch=True
                )
            else:
                self.logger.debug("Using single search for one embedding")
                results = self._perform_vector_search(embeddings[0], search_params)

            self.logger.info(f"Video search completed, found {len(results)} results")
            return results

        except (
            SearchRequestError,
            EmbeddingError,
            MediaProcessingError,
            DatabaseError,
        ):
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error in video search: {str(e)}")
            raise SearchError(f"Video search failed: {str(e)}")
