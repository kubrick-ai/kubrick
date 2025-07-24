import json
import logging
import os
import boto3
from embed_service import EmbedService
from vector_db_service import VectorDBService
from search_service import SearchService


logger = logging.getLogger()
logger.setLevel(logging.INFO)
secretsmanager = boto3.client("secretsmanager")


with open("config.json") as f:
    CONFIG = json.load(f)

try:
    sm_response = secretsmanager.get_secret_value(SecretId=CONFIG["secret_name"])
    SECRETS = json.loads(sm_response["SecretString"])
except Exception as e:
    logger.error(f"Failed to retrieve secret: {e}")
    raise

API_KEY = SECRETS["TWELVELABS_API_KEY"]

DB_CONFIG = {
    "host": os.getenv("DB_URL"),
    "database": "kubrick",
    "user": "postgres",
    "password": SECRETS["DB_PASSWORD"],
    "port": 5432,
}

embed_service = EmbedService(
    api_key=API_KEY,
    model_name=os.getenv("EMBEDDING_MODEL_NAME"),
    clip_length=os.getenv("DEFAULT_CLIP_LENGTH"),
)

vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)

search_service = SearchService(
    embed_service=embed_service, vector_db_service=vector_db_service
)


def lambda_handler(event, context):
    search_request = {
        "query_text": event.get("query_text"),
        "page_limit": event.get("page_limit"),
        "min_similarity": event.get("min_similarity"),
        "query_type": event.get("query_type"),
        "query_media_url": event.get("query_media_url"),
        "query_modality": event.get("query_modality"),
        "filter": event.get("filter"),
    }

    if search_request["query_type"] == "text":
        results = search_service.text_search(search_request=search_request)

    elif search_request["query_type"] == "image":
        results = search_service.image_search(search_request=search_request)

    elif search_request["query_type"] == "video":
        results = search_service.video_search(search_request=search_request)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": {
            "success": True,
            "data": json.dumps(results),
            "message": "Search completed successfully",
        },
    }
