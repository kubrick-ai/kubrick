import json
import os
import boto3
from twelvelabs import TwelveLabs, VideoSegment
from twelvelabs.embed import TasksStatusResponse
import psycopg2
from psycopg2.extras import RealDictCursor

# Assuming the queue URL for re-queuing is the same as the source queue,
# or you can get it from the event if needed.
QUEUE_URL = os.getenv("SQS_QUEUE_URL", "")
TWELVELABS_API_KEY = os.getenv("TWELVELABS_API_KEY", "")
DB_CONFIG = {
    "host": os.getenv("DB_URL"),
    "database": "kubrick",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD"),
    "port": 5432,
}

sqs_client = boto3.client("sqs")
tl_client = TwelveLabs(api_key=TWELVELABS_API_KEY)


def lambda_handler(event, context):
    failed_message_ids = []
    pending_message_ids = []
    successful_message_ids = []

    for record in event["Records"]:
        message_body = json.loads(record["body"])
        task_id = message_body.get("twelveLabsVideoEmbeddingTaskId")
        receipt_handle = record["receiptHandle"]

        try:
            # Call TwelveLabs API to get status
            task_status = get_task_status(task_id)

            if task_status == "ready":
                store(task_id)  # Your RDS insertion logic
                successful_message_ids.append(record["messageId"])
                # Lambda will automatically delete successful_message_ids if not in failed_message_ids
            elif task_status == "failed":
                failed_message_ids.append({"itemIdentifier": record["messageId"]})
                print(f"Task {task_id} failed.")
            elif task_status == "pending":
                # If status is "pending", add to failed list for re-queuing
                pending_message_ids.append({"itemIdentifier": record["messageId"]})
                # No explicit SQS send needed here, Lambda handles it
                print(f"Task {task_id} is still pending. Re-queueing.")
            else:
                raise Exception(f"Unexpected value for task status {task_status}")

        except Exception as e:
            print(f"Error processing task {task_id}: {e}")
            failed_message_ids.append({"itemIdentifier": record["messageId"]})

    # Return the list of pending message IDs
    if pending_message_ids:
        return {"batchItemFailures": pending_message_ids}
    else:
        return {}  # All messages processed successfully


def get_task_status(task_id):
    response = tl_client.embed.tasks.status(task_id=task_id)
    return response.status


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def _insert_video(cursor, metadata):
    cursor.execute(
        """
            INSERT INTO videos (url, filename, duration, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            RETURNING id
            """,
        (
            metadata["url"],
            metadata["filename"],
            metadata["duration"],
        ),
    )
    return cursor.fetchone()["id"]


def get_video_metadata(response):
    if response.video_embedding and response.video_embedding.metadata:
        md = response.video_embedding.metadata
        return {
            "url": md.input_url,
            "filename": md.input_filename,
            "duration": md.duration,
        }


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


def store(task_id):
    response = tl_client.embed.tasks.retrieve(task_id=task_id)
    video_metadata = get_video_metadata(response)
    if response.video_embedding is None or response.video_embedding.segments is None:
        raise Exception("No embedding returned from TwelveLabs API")

    video_segments = response.video_embedding.segments

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        video_id = _insert_video(cursor, video_metadata)
        _insert_video_segments(cursor, video_id, video_segments)
        conn.commit()
        print(f"Stored video and {len(video_segments)} embeddings.")

    except Exception as e:
        print("Error storing embedding:", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()
