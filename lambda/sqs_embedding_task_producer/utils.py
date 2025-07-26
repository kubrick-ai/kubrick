import os
import logging


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".flv",
    ".wmv",
    ".mpeg",
    ".mpg",
    ".mpe",
    ".m4v",
    ".3gp",
    ".ogv",
    ".ts",
    ".mxf",
}

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def is_valid_video_file(s3_key):
    valid = has_valid_file_extension(s3_key)
    if valid:
        logger.info(f"File '{s3_key}' has a valid video extension.")
    else:
        logger.warning(f"File '{s3_key}' does not have a valid video extension.")
    return valid


def has_valid_file_extension(s3_key):
    _, ext = os.path.splitext(s3_key.lower())
    logger.debug(f"Checking file extension: '{ext}'")
    return ext in VIDEO_EXTENSIONS


# TODO: This will eventually have to be moved to the embed service layer
def create_embedding_request(config, client, url):
    logger.info(f"Creating embedding task using model: {config['model_name']}")
    try:
        task = client.embed.tasks.create(
            model_name=config["model_name"],
            video_url=url,
            video_clip_length=config["clip_length"],
            video_embedding_scope=config["video_embedding_scopes"],
        )
        logger.info(f"Embedding task created with ID: {task.id}")
        return task.id
    except Exception as e:
        logger.error(f"Failed to create embedding request: {e}")
        raise
