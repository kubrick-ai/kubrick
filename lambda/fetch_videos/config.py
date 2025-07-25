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

        required_keys = ["presigned_url_expiry"]
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing required keys from config: {missing_keys}")

        return config

    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise