import urllib.parse
from config import load_config, get_secret, setup_logging, get_db_config
from vector_db_service import VectorDBService
from utils import is_valid_video_file


def lambda_handler(event, context):
    logger = setup_logging()
    config = load_config()
    SECRET = get_secret(config)
    DB_CONFIG = get_db_config(SECRET)

    vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)
    try:
        for record in event.get("Records", []):
            event_name = record.get("eventName", "")
            bucket = record.get("s3", {}).get("bucket", {}).get("name")
            key = urllib.parse.unquote_plus(
                record.get("s3", {}).get("object", {}).get("key", "")
            ).strip()

            if not bucket or not key:
                logger.warning("Missing bucket or key in S3 event record")
                continue

            logger.info(
                f"Processing event: {event_name}, S3 bucket: {bucket}, S3 key: {key}"
            )

            if not is_valid_video_file(key):
                logger.info(f"Ignoring non-video object S3 key: {key}")
                continue

            results = vector_db_service.fetch_video(bucket=bucket, key=key)

            if results:
                deleted = vector_db_service.delete_video(bucket=bucket, key=key)
                if deleted:
                    logger.info(
                        f"Deleted data for S3 key:{key} from S3 bucket: {bucket} from database."
                    )
                else:
                    logger.warning(
                        f"Failed to delete data for S3 key:{key} from S3 bucket: {bucket}. It might have been already removed."
                    )
            else:
                logger.info(
                    f"No data found in DB for deleted S3 object [bucket: {bucket}, key: {key}]"
                )

    except Exception as e:
        logger.exception("Unhandled exception in Lambda handler")
