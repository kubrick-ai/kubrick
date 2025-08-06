import json
import os
import boto3
from embed_service import EmbedService, VideoEmbeddingMetadata
from config import get_secret, setup_logging, get_db_config
from vector_db_service import VectorDBService

# Environment variables
SECRET_NAME = os.getenv("SECRET_NAME", "kubrick_secret")
QUEUE_URL = os.environ["QUEUE_URL"]
SQS_MESSAGE_VISIBILITY_TIMEOUT = int(os.getenv("SQS_MESSAGE_VISIBILITY_TIMEOUT", "25"))

SECRET = get_secret(SECRET_NAME)
DB_CONFIG = get_db_config(SECRET)

embed_service = EmbedService(
    api_key=SECRET["TWELVELABS_API_KEY"],
    model_name=os.getenv("EMBEDDING_MODEL_NAME", "Marengo-retrieval-2.7"),
    clip_length=int(os.getenv("DEFAULT_CLIP_LENGTH", 6)),
    logger=logger,
)
vector_db_service = VectorDBService(db_params=DB_CONFIG, logger=logger)
sqs = boto3.client("sqs")


def get_video_metadata(tl_metadata: VideoEmbeddingMetadata | None, message_body):
    metadata = {"filename": os.path.basename(message_body["s3_key"])}

    if tl_metadata:
        metadata["duration"] = tl_metadata.duration

    metadata["s3_bucket"] = message_body["s3_bucket"]
    metadata["s3_key"] = message_body["s3_key"]

    return metadata


def lambda_handler(event, context):
    logger = setup_logging()
    pending_message_ids = []
    for record in event["Records"]:
        message_id = record.get("messageId")
        receipt_handle = record.get("receiptHandle")
        try:
            message_body = json.loads(record["body"])
            tl_task_id = message_body.get("twelvelabs_video_embedding_task_id")
            # use receipt_handle to distinguish between different records representing the same message
            logger.info(f"Record receiptHandle: {receipt_handle}")

            task_status = embed_service.get_embedding_request_status(tl_task_id)

            if task_status == "ready":
                tl_response = embed_service.retrieve_embed_response(task_id=tl_task_id)
                logger.info("Extracting video metadata...")
                tl_metadata = embed_service.get_video_metadata(response=tl_response)
                video_metadata = get_video_metadata(tl_metadata, message_body)
                logger.info(f"Successfully extracted video metadata: {video_metadata}")

                logger.info("Normalizing segments...")
                video_segments = embed_service.normalize_segments(
                    tl_response.video_embedding.segments
                )

                vector_db_service.store(video_metadata, video_segments)
                logger.info("Successfully stored video and segments in DB")
                vector_db_service.update_task_status(message_id, "completed")
                logger.info("Successfully updated task status in DB")

            elif task_status == "failed":
                logger.error(f"TwelveLabs video embedding task failed: {message_body}")
                vector_db_service.update_task_status(message_id, "failed")
                logger.info("Successfully updated task status in DB")

            elif task_status == "processing":
                logger.info(
                    f"TwelveLabs video embedding task {tl_task_id} is still processing. Re-queueing."
                )
                # If status is "processing", add to pending list for re-queuing
                pending_message_ids.append({"itemIdentifier": message_id})
                sqs.change_message_visibility(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=receipt_handle,
                    VisibilityTimeout=SQS_MESSAGE_VISIBILITY_TIMEOUT,
                )
                vector_db_service.update_task_status(message_id, "processing")
                logger.info("Successfully updated task status in DB")
            else:
                raise Exception(f"Unexpected value for task status {task_status}")

        except Exception as e:
            logger.error(f"Error processing task {message_id}: {e}")
            pending_message_ids.append({"itemIdentifier": message_id})
            sqs.change_message_visibility(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=SQS_MESSAGE_VISIBILITY_TIMEOUT,
            )
            vector_db_service.update_task_status(message_id, "retrying")
            logger.info("Successfully updated task status in DB")

    # Return the list of pending message IDs
    if pending_message_ids:
        return {"batchItemFailures": pending_message_ids}
    else:
        return {}  # All messages processed successfully
