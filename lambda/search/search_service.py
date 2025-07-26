from embed_service import EmbedService
from vector_db_service import VectorDBService
from logging import getLogger


class SearchService:
    def __init__(
        self,
        embed_service: EmbedService,
        vector_db_service: VectorDBService,
        logger=getLogger(),
    ):
        self.embed_service = embed_service
        self.vector_db_service = vector_db_service
        self.logger = logger

    def text_search(self, search_request):
        self.logger.info(f"Starting text search with request: {search_request}")
        if search_request["query_text"]:
            self.logger.info(
                f"Extracting text embedding for: {search_request['query_text']}"
            )
            embedding = self.embed_service.extract_text_embedding(
                search_request["query_text"]
            )
            self.logger.info(
                f"Searching vector DB with embedding shape: {len(embedding) if embedding else 'None'}"
            )
            results = self.vector_db_service.find_similar(
                embedding=embedding,
                filter=search_request.get("filter", None),
                page_limit=search_request.get(
                    "page_limit", self.vector_db_service.default_page_limit
                ),
                min_similarity=search_request.get(
                    "min_similarity", self.vector_db_service.default_min_similarity
                ),
            )
            self.logger.info(
                f"Text search completed, found {len(results) if results else 0} results"
            )
            return results
        else:
            self.logger.error("Text search failed: No query_text provided")
            raise Exception("Expected a query text argument")

    def image_search(self, search_request):
        self.logger.info(f"Starting image search with request: {search_request}")
        if search_request["query_media_url"]:
            self.logger.info(
                f"Extracting image embedding from URL: {search_request['query_media_url']}"
            )
            embedding = self.embed_service.extract_image_embedding(
                url=search_request["query_media_url"]
            )
        elif search_request["query_media_file"]:
            self.logger.info(
                f"Extracting image embedding from file (size: {len(search_request['query_media_file']) if search_request['query_media_file'] else 'None'} bytes)"
            )
            embedding = self.embed_service.extract_image_embedding(
                file=search_request["query_media_file"]
            )
        else:
            self.logger.error(
                "Image search failed: No query_media_url or query_media_file provided"
            )
            raise Exception("Expected a file or url argument")

        self.logger.info(
            f"Searching vector DB with embedding shape: {len(embedding) if embedding else 'None'}"
        )

        results = self.vector_db_service.find_similar(
            embedding=embedding,
            filter=search_request.get("filter", None),
            page_limit=search_request.get(
                "page_limit", self.vector_db_service.default_page_limit
            ),
            min_similarity=search_request.get(
                "min_similarity", self.vector_db_service.default_min_similarity
            ),
        )
        self.logger.info(
            f"Image search completed, found {len(results) if results else 0} results"
        )
        return results

    def video_search(self, search_request):
        self.logger.info(f"Starting video search with request: {search_request}")
        if search_request["query_media_url"]:
            self.logger.info(
                f"Extracting video embedding from URL: {search_request['query_media_url']} with modality: {search_request['query_modality']}"
            )
            embeddings = self.embed_service.extract_video_embedding(
                url=search_request["query_media_url"],
                query_modality=search_request["query_modality"],
            )
        elif search_request["query_media_file"]:
            self.logger.info(
                f"Extracting video embedding from file (size: {len(search_request['query_media_file']) if search_request['query_media_file'] else 'None'} bytes) with modality: {search_request['query_modality']}"
            )
            embeddings = self.embed_service.extract_video_embedding(
                file=search_request["query_media_file"],
                query_modality=search_request["query_modality"],
            )
        else:
            self.logger.error(
                "Video search failed: No query_media_url or query_media_file provided"
            )
            raise Exception("Expected a file or url argument")

        self.logger.info(f"Extracted {len(embeddings)} embeddings from video")
        if len(embeddings) > 1:
            self.logger.info("Using batch search for multiple embeddings")
            results = self.vector_db_service.find_similar_batch(
                embeddings=embeddings,
                filter=search_request.get("filter", None),
                page_limit=search_request.get(
                    "page_limit", self.vector_db_service.default_page_limit
                ),
                min_similarity=search_request.get(
                    "min_similarity", self.vector_db_service.default_min_similarity
                ),
            )

        elif len(embeddings) == 1:
            self.logger.info("Using single search for one embedding")
            results = self.vector_db_service.find_similar(
                embedding=embeddings[0],
                filter=search_request.get("filter", None),
                page_limit=search_request.get(
                    "page_limit", self.vector_db_service.default_page_limit
                ),
                min_similarity=search_request.get(
                    "min_similarity", self.vector_db_service.default_min_similarity
                ),
            )
        else:
            self.logger.error("Video search failed: Could not extract video embeddings")
            raise Exception("Could not extract video embeddings.")

        self.logger.info(
            f"Video search completed, found {len(results) if results else 0} results"
        )
        return results
