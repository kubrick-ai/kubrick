import json
import logging
import os
from twelvelabs import TwelveLabs, VideoSegment
from twelvelabs.embed import TasksStatusResponse
from config import load_config, get_secret
from vector_db_service import VectorDBService


def get_embedding_provider_task_status(tl_client, task_id):
    response: TasksStatusResponse = tl_client.embed.tasks.status(task_id=task_id)
    return response.status


def get_video_metadata(response, message_body):
    metadata = {"filename": os.path.basename(message_body["s3_key"])}

    if response.video_embedding and response.video_embedding.metadata:
        md = response.video_embedding.metadata
        metadata["duration"] = md.duration

    metadata["s3_bucket"] = message_body["s3_bucket"]
    metadata["s3_key"] = message_body["s3_key"]

    return metadata


def normalize_segments(twelvelabs_segments: list[VideoSegment]):
    # Normalise segment data structure from TwelveLabs v1.0.0b0 VideoSegment type
    return [
        {
            "start_time": segment.start_offset_sec,
            "end_time": segment.end_offset_sec,
            "scope": segment.embedding_scope,  # "clip" or "video"
            "modality": segment.embedding_option,  # "text-visual" or "audio"
            "embedding": segment.float_,
        }
        for segment in twelvelabs_segments
    ]


def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    config = load_config()
    SECRET = get_secret(config)

    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DB_NAME", "kubrick"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": SECRET["DB_PASSWORD"],
        "port": 5432,
    }

    tl_client = TwelveLabs(api_key=SECRET["TWELVELABS_API_KEY"])
    db = VectorDBService(db_params=DB_CONFIG, logger=logger)

    pending_message_ids = []

    for record in event["Records"]:
        message_id = record["messageId"]
        try:
            message_body = json.loads(record["body"])
            tl_task_id = message_body.get("twelvelabs_video_embedding_task_id")
            # use receipt_handle to distinguish between different records representing the same message
            receipt_handle = record["receiptHandle"]
            logger.info(f"Record receiptHandle: {receipt_handle}")

            task_status = get_embedding_provider_task_status(tl_client, tl_task_id)

            if task_status == "ready":
                tl_response = tl_client.embed.tasks.retrieve(task_id=tl_task_id)

                if (
                    tl_response.video_embedding is None
                    or tl_response.video_embedding.segments is None
                ):
                    raise ValueError("No embedding returned from TwelveLabs API")

                logger.info("Extracting video metadata...")
                video_metadata = get_video_metadata(tl_response, message_body)
                logger.info(f"Successfully extracted video metadata: {video_metadata}")

                logger.info("Normalizing segments...")
                video_segments = normalize_segments(
                    tl_response.video_embedding.segments
                )

                db.store(video_metadata, video_segments)
                logger.info("Successfully stored video and segments in DB")

            elif task_status == "failed":
                logger.error(f"TwelveLabs video embedding task failed: {message_body}")

            elif task_status == "processing":
                # If status is "processing", add to pending list for re-queuing
                pending_message_ids.append({"itemIdentifier": message_id})
                logger.info(
                    f"TwelveLabs video embedding task {tl_task_id} is still pending. Re-queueing."
                )
            else:
                raise Exception(f"Unexpected value for task status {task_status}")

        except Exception as e:
            logger.error(f"Error processing task {message_id}: {e}")
            pending_message_ids.append({"itemIdentifier": message_id})

    # Return the list of pending message IDs
    if pending_message_ids:
        return {"batchItemFailures": pending_message_ids}
    else:
        return {}  # All messages processed successfully
