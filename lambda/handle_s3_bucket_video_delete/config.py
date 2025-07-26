import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def load_config(config_path="config.json"):
    try:
        logger.info("Loading config from config.json...")
        with open(config_path) as f:
            config = json.load(f)
        required_keys = [
            "model_name",
            "video_embedding_scopes",
            "secret_name",
            "clip_length",
            "presigned_url_ttl",
            "file_check_retries",
            "file_check_delay_sec",
        ]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing required keys from config: {missing_keys}")
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise


def get_secret(config, key="secret_name"):
    try:
        logger.info("Retrieving secret...")
        secretsmanager = boto3.client("secretsmanager")
        sm_response = secretsmanager.get_secret_value(SecretId=config[key])
        return json.loads(sm_response["SecretString"])
    except Exception as e:
        logger.error(f"Failed to retrieve secret: {e}")
        raise
