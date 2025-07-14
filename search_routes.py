from flask import Blueprint, jsonify, request
import tempfile
import embed
import vector_db

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=("POST",))
def search():
    """
    Expects a JSON body with the following properties:
        query_text: string (optional)
        query_media_type: "image" | "video" | "audio" (optional)
        query_media_url: string (optional)
        query_media_file: file (optional)
        page_limit: integer (optional)
        min_similarity: float (optional)
    """
    request_data = request.get_json()

    if not request_data:
        return jsonify({"error": "Invalid request body - must be a JSON object."}), 400

    query_text = request_data.get("query_text")
    query_media_type = request_data.get("query_media_type")
    page_limit = request_data.get("page_limit")
    min_similarity = request_data.get("min_similarity")
    # Currently only supporting one embedding source
    # TODO: should be able to search with multiple embeddings (text + some media)

    if query_media_type:
        query_media_url = request_data.get("query_media_url")
        query_media_file = request_data.get("query_media_file")
        if query_media_type == "video":
            if query_media_url:
                embeddings = embed.extract_video_embeddings(url=query_media_url)
            elif query_media_file:
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    embeddings = embed.extract_video_embeddings(filepath=f.filepath)
            else:
                return jsonify(
                    {
                        "error": "Invalid request body - If `query_media_type` is specified, request body must contain `query_media_url` or `query_media_file`."
                    }
                ), 400

    else:
        embeddings = [embed.extract_text_features(query_text)]

    results = vector_db.find_similar_batch(embeddings, page_limit, min_similarity)

    data = {
        "data": results,
    }
    return jsonify(data)
