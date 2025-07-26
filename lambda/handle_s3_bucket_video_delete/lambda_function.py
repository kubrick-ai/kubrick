import os
import boto3
import logging
from config import load_config, get_secret
from vector_db_service import VectorDBService

s3 = boto3.client("s3")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Lambda handler invoked")

    config = load_config()
    SECRET = get_secret(config)

    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "kubrick"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": SECRET["DB_PASSWORD"],
        "port": 5432,
    }

    db = VectorDBService(db_params=DB_CONFIG, logger=logger)
    