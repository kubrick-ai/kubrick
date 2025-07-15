from flask import Blueprint, jsonify, request
import tempfile

from app.services.embed_service import EmbedService
from app.services.vector_db_service import VectorDBService


def create_search_bp(embed_service: EmbedService, vector_db_service: VectorDBService):
    search_bp = Blueprint("search", __name__)

    @search_bp.route("/search", methods=("POST",))
    def search():
        """
        Expects multipart/form-data with the following fields:
            query_text: string (optional)
            query_media_type: "image" | "video" | "audio" (optional)
            query_media_url: string (optional)
            query_media_file: file (optional)
            page_limit: integer (optional)
            min_similarity: float (optional)
        """

        query_text = request.form.get("query_text")
        query_media_type = request.form.get("query_media_type")
        page_limit = request.form.get(
            "page_limit", vector_db_service.default_page_limit
        )
        min_similarity = request.form.get(
            "min_similarity", vector_db_service.default_min_similarity
        )

        # Convert string parameters to appropriate types
        page_limit = int(page_limit)
        min_similarity = float(min_similarity)

        # Currently only supporting one embedding source
        # TODO: should be able to search with multiple embeddings (text + some media)

        if query_media_type:
            query_media_url = request.form.get("query_media_url")
            query_media_file = request.files.get("query_media_file")
            embeddings = None
            if query_media_type == "image":
                if query_media_url:
                    embedding = embed_service.extract_image_embeddings(
                        url=query_media_url
                    )

                elif query_media_file:
                    embedding = embed_service.extract_image_embeddings(
                        file=query_media_file
                    )
                else:
                    return (
                        jsonify(
                            {
                                "error": "Invalid request body - If `query_media_type` is specified, request body must contain `query_media_url` or `query_media_file`."
                            }
                        ),
                        400,
                    )

                results = vector_db_service.find_similar(
                    embedding, page_limit, min_similarity
                )

            elif query_media_type == "video":
                if query_media_url:
                    embeddings = embed_service.extract_video_embedding(
                        url=query_media_url
                    )
                elif query_media_file:
                    # Save the uploaded file to a temporary location
                    with tempfile.NamedTemporaryFile() as temp_file:
                        query_media_file.save(temp_file.name)
                        embeddings = embed_service.extract_video_embedding(
                            filepath=temp_file.name
                        )
                else:
                    return (
                        jsonify(
                            {
                                "error": "Invalid request body - If `query_media_type` is specified, request body must contain `query_media_url` or `query_media_file`."
                            }
                        ),
                        400,
                    )

                results = vector_db_service.find_similar_batch(
                    embeddings, page_limit, min_similarity
                )

        else:
            if not query_text:
                return (
                    jsonify(
                        {
                            "error": "Invalid request body - If `query_media_type` is not specified, request body must contain `query_text`."
                        }
                    ),
                    400,
                )

            embedding = embed_service.extract_text_embeddings(query_text)
            results = vector_db_service.find_similar(embedding)

        data = {
            "data": results,
        }

        return jsonify(data)

    return search_bp
