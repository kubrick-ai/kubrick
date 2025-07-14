from flask import Blueprint, jsonify, request
import tempfile
import embed
import vector_db

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
    page_limit = request.form.get("page_limit", vector_db.DEFAULT_PAGE_LIMIT)
    min_similarity = request.form.get(
        "min_similarity", vector_db.DEFAULT_MIN_SIMILARITY
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
        if query_media_type == "video":
            if query_media_url:
                embeddings = embed.extract_video_embeddings(url=query_media_url)
            elif query_media_file:
                # Save the uploaded file to a temporary location
                with tempfile.NamedTemporaryFile() as temp_file:
                    query_media_file.save(temp_file.name)
                    embeddings = embed.extract_video_embeddings(filepath=temp_file.name)
            else:
                return jsonify(
                    {
                        "error": "Invalid request body - If `query_media_type` is specified, request body must contain `query_media_url` or `query_media_file`."
                    }
                ), 400

        results = vector_db.find_similar_batch(embeddings, page_limit, min_similarity)

    else:
        if not query_text:
            return jsonify(
                {
                    "error": "Invalid request body - If `query_media_type` is not specified, request body must contain `query_text`."
                }
            ), 400

        embedding = embed.extract_text_features(query_text)
        results = vector_db.find_similar(embedding)

    data = {
        "data": results,
    }
    return jsonify(data)
