import pytest
import json
from unittest.mock import patch, MagicMock

from sqs_embedding_task_consumer.lambda_function import (
    lambda_handler,
    get_video_metadata,
)


# Fixtures for Mocking Services and Utilities
@pytest.fixture
def mock_logger():
    """Mocks the global logger instance in the lambda function."""
    with patch("sqs_embedding_task_consumer.lambda_function.logger") as mock_logger:
        yield mock_logger


@pytest.fixture
def mock_embed_service():
    """Mocks the global embed_service instance in the lambda function."""
    with patch("sqs_embedding_task_consumer.lambda_function.embed_service") as mock_service:
        yield mock_service


@pytest.fixture
def mock_vector_db_service():
    """Mocks the global vector_db_service instance in the lambda function."""
    with patch("sqs_embedding_task_consumer.lambda_function.vector_db_service") as mock_service:
        yield mock_service


@pytest.fixture
def mock_sqs_client():
    """Mocks the global sqs client instance in the lambda function."""
    with patch("sqs_embedding_task_consumer.lambda_function.sqs") as mock_client:
        yield mock_client


# Test Functions
def test_lambda_handler_success_ready_status(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test successful processing when TwelveLabs task is 'ready'."""
    mock_task_id = "tl-task-123"
    message_id = "msg-1"
    s3_bucket = "test-bucket"
    s3_key = "videos/test_video.mp4"

    # Create SQS event using EventBuilder
    event = event_builder.sqs_event(
        [event_builder.sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)]
    )
    context = MagicMock()

    # Mock embed_service behavior for 'ready' status
    mock_embed_service.get_embedding_request_status.return_value = "ready"

    mock_tl_response = MagicMock()
    mock_tl_response.video_embedding.segments = [
        MagicMock(
            start_offset_sec=0,
            end_offset_sec=5,
            embedding_scope="clip",
            embedding_option="text-visual",
            float_=[0.1, 0.2],
        ),
        MagicMock(
            start_offset_sec=0,
            end_offset_sec=10,
            embedding_scope="video",
            embedding_option="text-visual",
            float_=[0.3, 0.4],
        ),
    ]
    mock_tl_response.video_embedding.metadata = MagicMock(duration=120)
    mock_embed_service.retrieve_embed_response.return_value = mock_tl_response
    mock_embed_service.get_video_metadata.return_value = MagicMock(duration=120)

    # Expected normalized segments
    expected_normalized_segments = [
        {
            "start_time": 0,
            "end_time": 5,
            "scope": "clip",
            "modality": "text-visual",
            "embedding": [0.1, 0.2],
        },
        {
            "start_time": 0,
            "end_time": 10,
            "scope": "video",
            "modality": "text-visual",
            "embedding": [0.3, 0.4],
        },
    ]
    mock_embed_service.normalize_segments.return_value = expected_normalized_segments

    response = lambda_handler(event, context)

    # Assertions
    mock_embed_service.get_embedding_request_status.assert_called_once_with(
        mock_task_id
    )
    mock_embed_service.retrieve_embed_response.assert_called_once_with(
        task_id=mock_task_id
    )
    mock_embed_service.get_video_metadata.assert_called_once_with(
        response=mock_tl_response
    )
    mock_embed_service.normalize_segments.assert_called_once_with(
        mock_tl_response.video_embedding.segments
    )

    expected_video_metadata = {
        "filename": "test_video.mp4",
        "duration": 120,
        "s3_bucket": s3_bucket,
        "s3_key": s3_key,
    }
    mock_vector_db_service.store.assert_called_once_with(
        expected_video_metadata, expected_normalized_segments
    )
    mock_vector_db_service.update_task_status.assert_called_once_with(
        message_id, "completed"
    )
    mock_logger.info.assert_any_call(
        "Successfully stored video and segments in DB"
    )
    mock_logger.info.assert_any_call("Successfully updated task status in DB")
    assert response == {}


def test_lambda_handler_failed_status(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test processing when TwelveLabs task is 'failed'."""
    mock_task_id = "tl-task-456"
    message_id = "msg-2"
    s3_bucket = "test-bucket"
    s3_key = "videos/another_video.mp4"

    event = event_builder.sqs_event(
        [event_builder.sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)]
    )
    context = MagicMock()

    mock_embed_service.get_embedding_request_status.return_value = "failed"

    response = lambda_handler(event, context)

    # Assertions
    mock_embed_service.get_embedding_request_status.assert_called_once_with(
        mock_task_id
    )
    mock_vector_db_service.update_task_status.assert_called_once_with(
        message_id, "failed"
    )
    mock_logger.error.assert_called_once()  # Should log the failure
    mock_logger.info.assert_any_call("Successfully updated task status in DB")
    assert response == {}


def test_lambda_handler_processing_status(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test processing when TwelveLabs task is 'processing' (re-queues message)."""
    mock_task_id = "tl-task-789"
    message_id = "msg-3"
    s3_bucket = "test-bucket"
    s3_key = "videos/yet_another_video.mp4"

    event = event_builder.sqs_event(
        [event_builder.sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)]
    )
    context = MagicMock()

    mock_embed_service.get_embedding_request_status.return_value = "processing"

    response = lambda_handler(event, context)

    # Assertions
    mock_embed_service.get_embedding_request_status.assert_called_once_with(
        mock_task_id
    )
    mock_vector_db_service.update_task_status.assert_called_once_with(
        message_id, "processing"
    )
    mock_logger.info.assert_any_call(
        f"TwelveLabs video embedding task {mock_task_id} is still processing. Re-queueing."
    )
    mock_logger.info.assert_any_call("Successfully updated task status in DB")
    assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}


def test_lambda_handler_general_exception(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test handling a general exception during message processing."""
    mock_task_id = "tl-task-101"
    message_id = "msg-4"
    s3_bucket = "test-bucket"
    s3_key = "videos/error_video.mp4"

    event = event_builder.sqs_event(
        [event_builder.sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)]
    )
    context = MagicMock()

    # Simulate an exception when getting task status
    mock_embed_service.get_embedding_request_status.side_effect = Exception(
        "API connection error"
    )

    response = lambda_handler(event, context)

    # Assertions
    mock_logger.error.assert_called_once_with(
        f"Error processing task {message_id}: API connection error"
    )
    mock_vector_db_service.update_task_status.assert_called_once_with(
        message_id, "retrying"
    )
    mock_logger.info.assert_any_call("Successfully updated task status in DB")
    assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}


def test_lambda_handler_multiple_records(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test handling multiple SQS records with different statuses."""
    event = event_builder.sqs_event(
        [
            event_builder.sqs_event_record("msg-10", "bucket", "key1.mp4", "tl-10"),
            event_builder.sqs_event_record("msg-11", "bucket", "key2.mp4", "tl-11"),
            event_builder.sqs_event_record("msg-12", "bucket", "key3.mp4", "tl-12"),
            event_builder.sqs_event_record("msg-13", "bucket", "key4.mp4", "tl-13"),
        ]
    )
    context = MagicMock()

    mock_embed_service.get_embedding_request_status.side_effect = [
        "ready",  # msg-10
        "failed",  # msg-11
        "processing",  # msg-12
        Exception("Simulated error for msg-13"),  # msg-13
    ]

    # Mocks for the 'ready' task (msg-10)
    mock_tl_response_ready = MagicMock()
    mock_tl_response_ready.video_embedding.segments = [
        MagicMock(
            start_offset_sec=0,
            end_offset_sec=10,
            embedding_scope="video",
            embedding_option="text-visual",
            float_=[0.5, 0.6],
        )
    ]
    mock_tl_response_ready.video_embedding.metadata = MagicMock(duration=90)
    mock_embed_service.retrieve_embed_response.return_value = mock_tl_response_ready
    mock_embed_service.get_video_metadata.return_value = MagicMock(duration=90)
    mock_embed_service.normalize_segments.return_value = [
        {
            "start_time": 0,
            "end_time": 90,
            "scope": "video",
            "modality": "text-visual",
            "embedding": [0.5, 0.6],
        }
    ]

    response = lambda_handler(event, context)

    # Assertions for each message
    # msg-10 (ready)
    mock_embed_service.get_embedding_request_status.assert_any_call("tl-10")
    mock_vector_db_service.update_task_status.assert_any_call("msg-10", "completed")

    # msg-11 (failed)
    mock_embed_service.get_embedding_request_status.assert_any_call("tl-11")
    mock_vector_db_service.update_task_status.assert_any_call("msg-11", "failed")

    # msg-12 (processing)
    mock_embed_service.get_embedding_request_status.assert_any_call("tl-12")
    mock_vector_db_service.update_task_status.assert_any_call("msg-12", "processing")

    # msg-13 (error)
    mock_embed_service.get_embedding_request_status.assert_any_call("tl-13")
    mock_vector_db_service.update_task_status.assert_any_call("msg-13", "retrying")

    # Verify batchItemFailures contains messages that failed or are still processing
    assert len(response["batchItemFailures"]) == 2
    assert {"itemIdentifier": "msg-12"} in response["batchItemFailures"]
    assert {"itemIdentifier": "msg-13"} in response["batchItemFailures"]


def test_lambda_handler_empty_records(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test handler with an empty 'Records' list."""
    event = event_builder.sqs_event([])
    context = MagicMock()

    response = lambda_handler(event, context)

    # No processing should happen, services should not be called
    mock_embed_service.get_embedding_request_status.assert_not_called()
    mock_vector_db_service.update_task_status.assert_not_called()
    assert response == {}


def test_lambda_handler_malformed_message_body(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test handling of a malformed SQS message body (json.loads fails)."""
    message_id = "msg-malformed"
    # Create malformed event manually since sqs_event_record creates valid JSON
    event = event_builder.sqs_event(
        [
            {
                "messageId": message_id,
                "receiptHandle": f"receipt-handle-{message_id}",
                "body": "{invalid json",  # Malformed JSON
                "attributes": {},
                "messageAttributes": {},
                "md5OfBody": "",
                "eventSource": "aws:sqs",
                "eventSourceARN": "",
                "awsRegion": "us-east-1",
            }
        ]
    )
    context = MagicMock()

    response = lambda_handler(event, context)

    mock_logger.error.assert_called_once()  # Should log the JSON decoding error
    mock_vector_db_service.update_task_status.assert_called_once_with(
        message_id, "retrying"
    )
    assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}


def test_get_video_metadata_none_tl_metadata():
    """Test get_video_metadata helper when tl_metadata is None."""
    message_body = {"s3_bucket": "test-bucket", "s3_key": "videos/no_metadata.mp4"}
    metadata = get_video_metadata(None, message_body)

    assert metadata == {
        "filename": "no_metadata.mp4",
        "s3_bucket": "test-bucket",
        "s3_key": "videos/no_metadata.mp4",
    }
    assert "duration" not in metadata


def test_lambda_handler_retrieve_embed_response_no_embedding_segments(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test scenario where retrieve_embed_response returns no video_embedding or segments."""
    mock_task_id = "tl-task-no-embed"
    message_id = "msg-no-embed"
    s3_bucket = "test-bucket"
    s3_key = "videos/no_embedding.mp4"

    event = event_builder.sqs_event(
        [event_builder.sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)]
    )
    context = MagicMock()

    mock_embed_service.get_embedding_request_status.return_value = "ready"
    # Simulate a response missing video_embedding or segments
    mock_tl_response_no_embed = MagicMock()
    mock_tl_response_no_embed.video_embedding = (
        None  # This causes AttributeError in lambda_function.py
    )
    mock_embed_service.retrieve_embed_response.return_value = mock_tl_response_no_embed

    response = lambda_handler(event, context)

    # Expect an error and message to be re-queued
    mock_logger.error.assert_called_once_with(
        f"Error processing task {message_id}: 'NoneType' object has no attribute 'segments'"
    )
    mock_vector_db_service.update_task_status.assert_called_once_with(
        message_id, "retrying"
    )
    assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}


def test_lambda_handler_db_store_failure(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test scenario where vector_db_service.store fails."""
    mock_task_id = "tl-task-db-fail"
    message_id = "msg-db-fail"
    s3_bucket = "test-bucket"
    s3_key = "videos/db_fail_video.mp4"

    event = event_builder.sqs_event(
        [event_builder.sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)]
    )
    context = MagicMock()

    mock_embed_service.get_embedding_request_status.return_value = "ready"

    mock_tl_response = MagicMock()
    mock_tl_response.video_embedding.segments = [
        MagicMock(
            start_offset_sec=0,
            end_offset_sec=5,
            embedding_scope="clip",
            embedding_option="text-visual",
            float_=[0.1, 0.2],
        )
    ]
    mock_tl_response.video_embedding.metadata = MagicMock(duration=120)
    mock_embed_service.retrieve_embed_response.return_value = mock_tl_response
    mock_embed_service.get_video_metadata.return_value = MagicMock(duration=120)
    mock_embed_service.normalize_segments.return_value = [
        {
            "start_time": 0,
            "end_time": 5,
            "scope": "clip",
            "modality": "text-visual",
            "embedding": [0.1, 0.2],
        }
    ]

    # Simulate database store failure
    mock_vector_db_service.store.side_effect = Exception("Database write error")

    response = lambda_handler(event, context)

    # The message should be re-queued because the store failed
    mock_logger.error.assert_called_once_with(
        f"Error processing task {message_id}: Database write error"
    )
    mock_vector_db_service.update_task_status.assert_called_once_with(
        message_id, "retrying"
    )
    assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}


def test_lambda_handler_db_update_task_status_failure(
    mock_logger,
    mock_embed_service,
    mock_vector_db_service,
    mock_sqs_client,
    event_builder,
):
    """Test scenario where vector_db_service.update_task_status fails."""
    mock_task_id = "tl-task-update-fail"
    message_id = "msg-update-fail"
    s3_bucket = "test-bucket"
    s3_key = "videos/update_fail_video.mp4"

    event = event_builder.sqs_event(
        [event_builder.sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)]
    )
    context = MagicMock()

    mock_embed_service.get_embedding_request_status.return_value = "ready"

    mock_tl_response = MagicMock()
    mock_tl_response.video_embedding.segments = [
        MagicMock(
            start_offset_sec=0,
            end_offset_sec=5,
            embedding_scope="clip",
            embedding_option="text-visual",
            float_=[0.1, 0.2],
        )
    ]
    mock_tl_response.video_embedding.metadata = MagicMock(duration=120)
    mock_embed_service.retrieve_embed_response.return_value = mock_tl_response
    mock_embed_service.get_video_metadata.return_value = MagicMock(duration=120)
    mock_embed_service.normalize_segments.return_value = [
        {
            "start_time": 0,
            "end_time": 5,
            "scope": "clip",
            "modality": "text-visual",
            "embedding": [0.1, 0.2],
        }
    ]

    # Simulate update_task_status failure after successful store
    # First call (completed) fails, second call (retrying) succeeds
    mock_vector_db_service.update_task_status.side_effect = [
        Exception("Database update error"),
        None,
    ]

    response = lambda_handler(event, context)

    # Verify the logger was called with the error and the update_task_status was called for retrying
    mock_logger.error.assert_called_once_with(
        f"Error processing task {message_id}: Database update error"
    )
    mock_vector_db_service.update_task_status.assert_called_with(
        message_id, "retrying"
    )  # Last call should be 'retrying'
    assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}
