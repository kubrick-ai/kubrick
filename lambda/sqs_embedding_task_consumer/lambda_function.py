import json
import time
import logging
import os
from twelvelabs import TwelveLabs, VideoSegment
from twelvelabs.embed import TasksStatusResponse
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
from config import load_config, get_secret

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_embedding_provider_task_status(tl_client, task_id):
    response: TasksStatusResponse = tl_client.embed.tasks.status(task_id=task_id)
    return response.status


def get_db_connection(db_config: dict, max_retries=3) -> connection:
    attempt = 0
    while True:
        try:
            logger.info("Connecting to database...")
            return psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
        except psycopg2.OperationalError as e:
            attempt += 1
            if attempt == max_retries - 1:
                logger.error(
                    f"Failed to connect to database after {attempt + 1} attempts: {e}"
                )
                raise
            logger.warning(
                f"Database connection attempt {attempt + 1} failed. Retrying..."
            )
            time.sleep(2**attempt)


def _insert_video(cursor, metadata):
    cursor.execute(
        """
            INSERT INTO videos (s3_bucket, s3_key, filename, duration, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            RETURNING id
            """,
        (
            metadata["s3_bucket"],
            metadata["s3_key"],
            metadata["filename"],
            metadata["duration"],
        ),
    )
    return cursor.fetchone()["id"]


def get_video_metadata(response):
    if response.video_embedding and response.video_embedding.metadata:
        md = response.video_embedding.metadata
        return {
            "filename": md.input_filename,
            "duration": md.duration,
        }
    return {}


def _insert_video_segments(cursor, video_id: int, segments: list[VideoSegment]):
    data_to_insert = [
        (
            video_id,
            segment.embedding_option,
            segment.embedding_scope,
            segment.start_offset_sec,
            segment.end_offset_sec,
            segment.float_,
        )
        for segment in segments
    ]

    cursor.executemany(
        """
       INSERT INTO video_segments (
           video_id,
           modality,
           scope,
           start_time,
           end_time,
           embedding
       ) VALUES (%s, %s, %s, %s, %s, %s)
       """,
        data_to_insert,
    )


def store(tl_client, db_connection, message_body):
    task_id = message_body["twelvelabs_video_embedding_task_id"]
    if not task_id:
        raise ValueError("Failed to find twelvelabs_video_embedding_task_id")

    response = tl_client.embed.tasks.retrieve(task_id=task_id)

    if response.video_embedding is None or response.video_embedding.segments is None:
        raise ValueError("No embedding returned from TwelveLabs API")

    video_metadata = get_video_metadata(response)
    video_metadata["s3_bucket"] = message_body["s3_bucket"]
    video_metadata["s3_key"] = message_body["s3_key"]

    video_segments = response.video_embedding.segments

    with db_connection.cursor() as cursor:
        try:
            video_id = _insert_video(cursor, video_metadata)
            _insert_video_segments(cursor, video_id, video_segments)
            db_connection.commit()
            logger.info(f"Stored video and {len(video_segments)} embeddings.")

        except Exception as e:
            logger.error("Error storing embedding:", e)
            db_connection.rollback()


def lambda_handler(event, context):
    config = load_config()
    SECRET = get_secret(config)
    tl_client = TwelveLabs(api_key=SECRET["TWELVELABS_API_KEY"])
    logger.info("Established TL client")

    DB_CONFIG = {
        "host": os.getenv("DB_URL"),
        "database": "kubrick",
        "user": "postgres",
        "password": SECRET["DB_PASSWORD"],
        "port": 5432,
    }

    with get_db_connection(DB_CONFIG) as conn:
        pending_message_ids = []

        for record in event["Records"]:
            message_body = json.loads(record["body"])
            task_id = message_body.get("twelvelabs_video_embedding_task_id")
            # use receipt_handle to distinguish between different records representing the same message
            # receipt_handle = record["receiptHandle"]

            try:
                task_status = get_embedding_provider_task_status(tl_client, task_id)

                if task_status == "ready":
                    store(tl_client, conn, message_body)

                elif task_status == "failed":
                    logger.error(
                        f"TwelveLabs video embedding task failed: {message_body}"
                    )

                elif task_status == "processing":
                    # If status is "processing", add to pending list for re-queuing
                    pending_message_ids.append({"itemIdentifier": record["messageId"]})
                    logger.info(
                        f"TwelveLabs video embedding task {task_id} is still pending. Re-queueing."
                    )
                else:
                    raise Exception(f"Unexpected value for task status {task_status}")

            except Exception as e:
                logger.error(f"Error processing task {task_id}: {e}")
                pending_message_ids.append({"itemIdentifier": record["messageId"]})

    # Return the list of pending message IDs
    if pending_message_ids:
        return {"batchItemFailures": pending_message_ids}
    else:
        return {}  # All messages processed successfully
