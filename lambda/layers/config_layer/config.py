import json
import logging
import boto3
import os
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)



def get_secret(secret_name: str = "kubrick_secret") -> Dict[str, Any]:
    """Retrieve secret from AWS Secrets Manager."""

    try:
        logger.info("Retrieving secret...")
        secretsmanager = boto3.client("secretsmanager")
        sm_response = secretsmanager.get_secret_value(SecretId=secret_name)
        return json.loads(sm_response["SecretString"])
    except Exception as e:
        logger.error(f"Failed to retrieve secret: {e}")
        raise


def setup_logging() -> logging.Logger:
    """
    Configure logging level from environment variable.
    Environment Variables:
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR), defaults to INFO
    """

    logger = logging.getLogger()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    try:
        logger.setLevel(log_level)
    except ValueError:
        logger.setLevel(logging.INFO)

    return logger


def get_db_config(secret: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get database configuration from environment variables and a secret.
    Environment Variables:
        DB_HOST     : Database host, defaults to localhost
        DB_NAME     : Database name, defaults to kubrick
        DB_USERNAME : Database user, defaults to postgres
        DB_PASSWORD : Database password, defaults to password
        DB_PORT     : Database port, defaults to 5432
    """

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "kubrick"),
        "user": secret.get("DB_USERNAME", os.getenv("DB_USERNAME", "postgres")),
        "password": secret.get("DB_PASSWORD", os.getenv("DB_PASSWORD", "password")),
        "port": int(os.getenv("DB_PORT", 5432)),
    }
