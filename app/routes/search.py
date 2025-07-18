import json
import tempfile

from app.services.embed_service import EmbedService
from app.services.vector_db_service import VectorDBService
from flask import Blueprint, jsonify, request


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
            query_modality: "visual-text" | "audio" (default: "visual-text", optional)
            operator: "or" | "and" (default: "or") (optional) NOT BEING USED
            filter: JSON (optional)
        """

        query_text = request.form.get("query_text")
        query_media_type = request.form.get("query_media_type")
        page_limit = request.form.get(
            "page_limit", vector_db_service.default_page_limit
        )
        min_similarity = request.form.get(
            "min_similarity", vector_db_service.default_min_similarity
        )
        query_modality = request.form.getlist("query_modality") or ["visual-text"]

        # operator = request.form.get("operator", "or") TODO: Add operator functionality
        filter = request.form.get("filter", None)

        if filter:
            filter = json.loads(filter)

        # Convert string parameters to appropriate types
        page_limit = int(page_limit)
        min_similarity = float(min_similarity)

        # Currently only supporting one embedding source
        # TODO: should be able to search with multiple embeddings (text + some media)

        if query_media_type:
            query_media_url = request.form.get("query_media_url")
            query_media_file = request.files.get("query_media_file")
            # embeddings = None
            if query_media_type == "image":
                if query_media_url:
                    embedding = embed_service.extract_image_embedding(
                        url=query_media_url
                    )

                elif query_media_file:
                    embedding = embed_service.extract_image_embedding(
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
                    embedding=embedding,
                    page_limit=page_limit,
                    min_similarity=min_similarity,
                    filter=filter,
                )

            elif query_media_type == "video":
                if query_media_url:
                    embeddings = embed_service.extract_video_embedding(
                        url=query_media_url, query_modality=query_modality
                    )
                elif query_media_file:
                    # Save the uploaded file to a temporary location
                    with tempfile.NamedTemporaryFile() as temp_file:
                        query_media_file.save(temp_file.name)
                        embeddings = embed_service.extract_video_embedding(
                            filepath=temp_file.name, query_modality=query_modality
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

                if len(embeddings) > 1:
                    results = vector_db_service.find_similar_batch(
                        embeddings=embeddings,
                        page_limit=page_limit,
                        min_similarity=min_similarity,
                    )

                elif len(embeddings) == 1:
                    results = vector_db_service.find_similar(
                        embedding=embeddings[0],
                        page_limit=page_limit,
                        min_similarity=min_similarity,
                        filter=filter,
                    )
                else:
                    raise Exception("Could not extract video embeddings.")

            else:
                return (
                    jsonify(
                        {
                            "error": "Invalid request body - `query_media_type` value must be `image` or `video`."
                        }
                    ),
                    400,
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

            embedding = embed_service.extract_text_embedding(query_text)
            results = vector_db_service.find_similar(
                embedding=embedding,
                filter=filter,
                page_limit=page_limit,
                min_similarity=min_similarity,
            )

        data = {"data": results}

        return jsonify(data)

    return search_bp
