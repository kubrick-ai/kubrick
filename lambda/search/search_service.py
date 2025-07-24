from embed_service import EmbedService
from vector_db_service import VectorDBService
import tempfile


class SearchService:
    def __init__(self, embed_service: EmbedService, vector_db_service: VectorDBService):
        self.embed_service = embed_service
        self.vector_db_service = vector_db_service

    def text_search(self, search_request):
        if search_request["query_text"]:
            embedding = self.embed_service.extract_text_embedding(
                search_request["query_text"]
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

            return results
        else:
            raise Exception("Expected a query text argument")

    def image_search(self, search_request):
        if search_request["query_media_url"]:
            embedding = self.embed_service.extract_image_embedding(
                url=search_request["query_media_url"]
            )
        elif search_request["query_media_file"]:
            embedding = self.embed_service.extract_image_embedding(
                file=search_request["query_media_file"]
            )
        else:
            raise Exception("Expected a file or url argument")

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

        return results

    def video_search(self, search_request):
        if search_request["query_media_url"]:
            embeddings = self.embed_service.extract_video_embedding(
                url=search_request["query_media_url"],
                query_modality=search_request["query_modality"],
            )
        elif search_request["query_media_file"]:
            with tempfile.NamedTemporaryFile() as temp_file:
                search_request["query_media_file"].save(temp_file.name)
                embeddings = self.embed_service.extract_video_embedding(
                    filepath=temp_file.name,
                    query_modality=search_request["query_modality"],
                )
        else:
            raise Exception("Expected a file or url argument")

        if len(embeddings) > 1:
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
            raise Exception("Could not extract video embeddings.")

        return results
