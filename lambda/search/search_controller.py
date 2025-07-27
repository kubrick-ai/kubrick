from embed_service import EmbedService
from vector_db_service import VectorDBService
from logging import getLogger, Logger
from typing import Dict, List, Any, Optional, Union
from response_utils import generate_presigned_url
from search_errors import (
    SearchError,
    SearchRequestError,
    EmbeddingError,
    DatabaseError,
    MediaProcessingError,
)


class SearchController:
    def __init__(
        self,
        embed_service: EmbedService,
        vector_db_service: VectorDBService,
        logger: Logger = getLogger(),
    ):
        self.embed_service = embed_service
        self.vector_db_service = vector_db_service
        self.logger = logger

    def _add_url(self, result):
        """Add presigned URL to search result"""
        result["video"]["url"] = generate_presigned_url(
            bucket=result["video"]["s3_bucket"], key=result["video"]["s3_key"]
        )
        return result

    def process_search_request(self, search_request_dict: Dict[str, Any]) -> List[Any]:
        """Process search request from parsed data to results with URLs"""
        try:
            self.logger.info("Processing search request")

            match query_type := search_request_dict.get("query_type"):
                case "text":
                    results = self.text_search(search_request=search_request_dict)
                case "image":
                    results = self.image_search(search_request=search_request_dict)
                case "video":
                    results = self.video_search(search_request=search_request_dict)
                case "audio":
                    raise SearchRequestError("Audio search is not yet implemented")
                case _:
                    raise SearchRequestError(f"Unsupported query_type: {query_type}")

            # Add URLs to results
            try:
                results_with_urls = [self._add_url(result) for result in results]
                self.logger.info(
                    f"Successfully processed search request, returning {len(results_with_urls)} results"
                )
                return results_with_urls
            except Exception as e:
                self.logger.error(f"Error adding URLs to results: {str(e)}")
                raise SearchError(f"Failed to process search results: {str(e)}")

        except SearchError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error processing search request: {str(e)}")
            raise SearchError(f"Search request processing failed: {str(e)}")

    def _extract_search_params(self, search_request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract common search parameters with defaults"""
        return {
            "filter": search_request.get("filter", None),
            "page_limit": search_request.get(
                "page_limit", self.vector_db_service.default_page_limit
            ),
            "min_similarity": search_request.get(
                "min_similarity", self.vector_db_service.default_min_similarity
            ),
        }

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
            self.logger.error(f"Unexpected error during vector search: {str(e)}")
            details = {
                "search_type": "batch" if use_batch else "single",
                "embedding_count": len(embedding) if use_batch else 1,
                "search_params": search_params,
            }
            raise DatabaseError(f"Vector database search failed: {str(e)}", details)

    def _validate_text_request(self, search_request: Dict[str, Any]) -> None:
        """Validate text search request"""
        query_text = search_request.get("query_text")
        if not query_text:
            raise SearchRequestError("query_text is required for text search")
        if not isinstance(query_text, str):
            raise SearchRequestError("query_text must be a string")
        if len(query_text.strip()) == 0:
            raise SearchRequestError("query_text cannot be empty")

    def _validate_media_request(self, search_request: Dict[str, Any]) -> None:
        """Validate media search request"""
        media_url = search_request.get("query_media_url")
        media_file = search_request.get("query_media_file")

        if not media_url and not media_file:
            raise SearchRequestError(
                "Either query_media_url or query_media_file is required"
            )

        if media_url and not isinstance(media_url, str):
            raise SearchRequestError("query_media_url must be a string")

        if media_file and not isinstance(media_file, bytes):
            raise SearchRequestError("query_media_file must be bytes")

    def _validate_video_request(self, search_request: Dict[str, Any]) -> None:
        """Validate video search request"""
        self._validate_media_request(search_request)

        query_modality = search_request.get("query_modality")
        if not query_modality:
            raise SearchRequestError("query_modality is required for video search")
        if not isinstance(query_modality, list):
            raise SearchRequestError("query_modality must be a list")
        if not all(isinstance(mod, str) for mod in query_modality):
            raise SearchRequestError("All query_modality values must be strings")

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
            self.logger.error(
                f"Unexpected error during text embedding extraction: {str(e)}"
            )
            raise EmbeddingError(
                f"Failed to extract text embedding: {str(e)}",
                {"query_length": len(query_text)},
            )

    def _extract_image_embedding(self, search_request: Dict[str, Any]) -> List[float]:
        """Extract image embedding from URL or file"""
        try:
            media_url = search_request.get("query_media_url")
            media_file = search_request.get("query_media_file")

            if media_url:
                self.logger.info(f"Extracting image embedding from URL")
                self.logger.debug(f"Image URL: {media_url}")
                embedding = self.embed_service.extract_image_embedding(url=media_url)
            else:
                file_size = len(media_file) if media_file else 0
                self.logger.info(
                    f"Extracting image embedding from file (size: {file_size} bytes)"
                )
                if file_size == 0:
                    raise MediaProcessingError("Image file is empty")
                embedding = self.embed_service.extract_image_embedding(file=media_file)

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
            self.logger.error(
                f"Unexpected error during image embedding extraction: {str(e)}"
            )
            details = {"source": "url" if media_url else "file"}
            if media_url:
                details["url_length"] = len(media_url)
            else:
                details["file_size"] = len(media_file) if media_file else 0
            raise EmbeddingError(
                f"Failed to extract image embedding: {str(e)}", details
            )

    def _extract_video_embeddings(
        self, search_request: Dict[str, Any]
    ) -> List[List[float]]:
        """Extract video embeddings from URL or file"""
        try:
            media_url = search_request.get("query_media_url")
            media_file = search_request.get("query_media_file")
            query_modality = search_request["query_modality"]

            if media_url:
                self.logger.info(
                    f"Extracting video embedding from URL with modality: {query_modality}"
                )
                self.logger.debug(f"Video URL: {media_url}")
                embeddings = self.embed_service.extract_video_embedding(
                    url=media_url, query_modality=query_modality
                )
            else:
                file_size = len(media_file) if media_file else 0
                self.logger.info(
                    f"Extracting video embedding from file (size: {file_size} bytes) with modality: {query_modality}"
                )
                if file_size == 0:
                    raise MediaProcessingError("Video file is empty")
                embeddings = self.embed_service.extract_video_embedding(
                    file=media_file, query_modality=query_modality
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
            self.logger.error(
                f"Unexpected error during video embedding extraction: {str(e)}"
            )
            details = {
                "source": "url" if media_url else "file",
                "modality": query_modality,
            }
            if media_url:
                details["url_length"] = len(media_url)
            else:
                details["file_size"] = len(media_file) if media_file else 0
            raise EmbeddingError(
                f"Failed to extract video embeddings: {str(e)}", details
            )

    def text_search(self, search_request: Dict[str, Any]) -> List[Any]:
        try:
            self.logger.info("Starting text search")

            self._validate_text_request(search_request)
            embedding = self._extract_text_embedding(search_request["query_text"])
            search_params = self._extract_search_params(search_request)
            results = self._perform_vector_search(embedding, search_params)

            self.logger.info(f"Text search completed, found {len(results)} results")
            return results

        except (SearchRequestError, EmbeddingError, DatabaseError):
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in text search: {str(e)}")
            raise SearchError(f"Text search failed: {str(e)}")

    def image_search(self, search_request: Dict[str, Any]) -> List[Any]:
        try:
            self.logger.info("Starting image search")

            self._validate_media_request(search_request)
            embedding = self._extract_image_embedding(search_request)
            search_params = self._extract_search_params(search_request)
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
            self.logger.error(f"Unexpected error in image search: {str(e)}")
            raise SearchError(f"Image search failed: {str(e)}")

    def video_search(self, search_request: Dict[str, Any]) -> List[Any]:
        try:
            self.logger.info("Starting video search")

            self._validate_video_request(search_request)
            embeddings = self._extract_video_embeddings(search_request)

            if not embeddings:
                raise EmbeddingError("Could not extract video embeddings")

            search_params = self._extract_search_params(search_request)

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
            self.logger.error(f"Unexpected error in video search: {str(e)}")
            raise SearchError(f"Video search failed: {str(e)}")
