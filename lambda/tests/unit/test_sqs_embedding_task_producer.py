import pytest
from unittest.mock import patch, MagicMock

from sqs_embedding_task_producer.lambda_function import (
    lambda_handler,
    persist_task_metadata,
)


# Comment
# Fixtures for Mocking Services and Utilities
@pytest.fixture
def mock_sqs_client():
    """Mocks the SQS client instance in the lambda function."""
    with patch("sqs_embedding_task_producer.lambda_function.sqs") as mock_sqs:
        mock_sqs.send_message.return_value = {"MessageId": "test-message-id-12345"}
        yield mock_sqs


@pytest.fixture
def mock_embed_service():
    """Mocks the global embed_service instance in the lambda function."""
    with patch("sqs_embedding_task_producer.lambda_function.embed_service") as mock_service:
        mock_task = MagicMock()
        mock_task.id = "test-task-12345"
        mock_service.create_embedding_request.return_value = mock_task
        yield mock_service


@pytest.fixture
def mock_vector_db():
    """Mocks the global vector_db_service instance in the lambda function."""
    with patch("sqs_embedding_task_producer.lambda_function.vector_db_service") as mock_service:
        yield mock_service


@pytest.fixture
def mock_wait_for_file():
    """Mocks the s3_utils.wait_for_file utility, defaulting to success."""
    with patch(
        "sqs_embedding_task_producer.lambda_function.s3_utils.wait_for_file"
    ) as mock_func:
        mock_func.return_value = True
        yield mock_func


@pytest.fixture
def mock_presigned_url():
    """Mocks the s3_utils.generate_presigned_url utility."""
    with patch(
        "sqs_embedding_task_producer.lambda_function.s3_utils.generate_presigned_url"
    ) as mock_func:
        mock_func.return_value = "https://test-presigned-url.com"
        yield mock_func


# Main Handler Tests
@pytest.mark.parametrize(
    "video_file",
    ["test.mp4", "test.mov", "test.avi", "test.mkv", "test.webm"],
)
def test_lambda_handler_success(
    mock_sqs_client,
    mock_embed_service,
    mock_vector_db,
    mock_wait_for_file,
    mock_presigned_url,
    kubrick_secret,
    test_sqs_queue,
    test_s3_bucket,
    event_builder,
    video_file,
):
    """Test successful processing of various supported video files."""
    s3_key = f"videos/{video_file}"
    event = event_builder.s3_event(bucket_name=test_s3_bucket, object_key=s3_key)
    response = lambda_handler(event, {})

    assert response["status"] == "success"
    assert response["task_id"] == "test-task-12345"
    assert response["s3_bucket"] == test_s3_bucket
    assert response["s3_key"] == s3_key
    assert response["sqs_message_id"] == "test-message-id-12345"

    mock_embed_service.create_embedding_request.assert_called_once()
    mock_vector_db.store_task.assert_called_once()
    mock_wait_for_file.assert_called_once()
    mock_presigned_url.assert_called_once()


@pytest.mark.parametrize(
    "invalid_file", ["document.pdf", "image.jpg", "audio.mp3", "archive.zip"]
)
def test_lambda_handler_unsupported_file_type(
    mock_sqs_client,
    mock_vector_db,
    kubrick_secret,
    test_sqs_queue,
    test_s3_bucket,
    event_builder,
    invalid_file,
):
    """Test that non-video files are marked as failed and not processed."""
    event = event_builder.s3_event(
        bucket_name=test_s3_bucket, object_key=f"uploads/{invalid_file}"
    )
    response = lambda_handler(event, {})

    assert response["status"] == "error"
    assert "not a video" in response["message"]
    mock_vector_db.store_task.assert_called_once()
    call_args = mock_vector_db.store_task.call_args[0][0]
    assert call_args["status"] == "failed"


def test_lambda_handler_ignores_folder_creation(
    mock_sqs_client,
    mock_embed_service,
    mock_vector_db,
    kubrick_secret,
    test_sqs_queue,
    test_s3_bucket,
    event_builder,
):
    """Test that S3 folder creation events (keys ending in '/') are ignored."""
    event = event_builder.s3_event(bucket_name=test_s3_bucket, object_key="videos/")
    response = lambda_handler(event, {})

    assert response["status"] == "ignored"
    mock_embed_service.create_embedding_request.assert_not_called()
    mock_vector_db.store_task.assert_not_called()


def test_lambda_handler_file_not_found(
    mock_sqs_client,
    mock_vector_db,
    mock_wait_for_file,
    kubrick_secret,
    test_sqs_queue,
    test_s3_bucket,
    event_builder,
):
    """Test failure when the S3 file is not found after retries."""
    mock_wait_for_file.return_value = False  # Simulate file not found
    event = event_builder.s3_event(
        bucket_name=test_s3_bucket, object_key="videos/missing.mp4"
    )
    response = lambda_handler(event, {})

    assert response["status"] == "error"
    assert "not found after retries" in response["message"]
    mock_vector_db.store_task.assert_called_once()
    assert mock_vector_db.store_task.call_args[0][0]["status"] == "failed"


def test_lambda_handler_embed_service_failure(
    mock_sqs_client,
    mock_embed_service,
    mock_vector_db,
    mock_wait_for_file,
    kubrick_secret,
    test_sqs_queue,
    test_s3_bucket,
    event_builder,
):
    """Test failure when the embedding service raises an exception."""
    mock_embed_service.create_embedding_request.side_effect = Exception(
        "TwelveLabs API error"
    )
    event = event_builder.s3_event(
        bucket_name=test_s3_bucket, object_key="videos/test.mp4"
    )
    response = lambda_handler(event, {})

    assert response["status"] == "error"
    assert "TwelveLabs API error" in response["message"]
    mock_vector_db.store_task.assert_called_once()


def test_lambda_handler_sqs_send_failure(
    mock_sqs_client,
    mock_embed_service,
    mock_vector_db,
    mock_wait_for_file,
    kubrick_secret,
    test_s3_bucket,
    event_builder,
    monkeypatch,
):
    """Test failure when sending the message to SQS fails."""
    from botocore.exceptions import ClientError

    mock_sqs_client.send_message.side_effect = ClientError(
        {"Error": {"Code": "NonExistentQueue", "Message": "Queue does not exist"}},
        "SendMessage",
    )
    event = event_builder.s3_event(
        bucket_name=test_s3_bucket, object_key="videos/test.mp4"
    )
    response = lambda_handler(event, {})

    assert response["status"] == "error"
    assert "Queue does not exist" in response["message"]
    mock_vector_db.store_task.assert_called_once()


def test_lambda_handler_db_store_failure(
    mock_sqs_client,
    mock_embed_service,
    mock_vector_db,
    mock_wait_for_file,
    kubrick_secret,
    test_sqs_queue,
    test_s3_bucket,
    event_builder,
):
    """Test that the handler succeeds even if storing task metadata fails."""
    mock_vector_db.store_task.side_effect = Exception("Database connection failed")
    event = event_builder.s3_event(
        bucket_name=test_s3_bucket, object_key="videos/test.mp4"
    )
    response = lambda_handler(event, {})

    assert response["status"] == "success"
    assert response["task_id"] == "test-task-12345"
    mock_vector_db.store_task.assert_called_once()


def test_lambda_handler_secrets_failure(
    mock_sqs_client, mock_embed_service, mock_wait_for_file, mock_presigned_url, event_builder, test_s3_bucket, test_sqs_queue
):
    """Test failure when embed service throws an exception due to missing API key."""
    mock_embed_service.create_embedding_request.side_effect = KeyError("TWELVELABS_API_KEY")
    event = event_builder.s3_event(
        bucket_name=test_s3_bucket, object_key="videos/test.mp4"
    )
    response = lambda_handler(event, {})
    assert response["status"] == "error"
    assert "TWELVELABS_API_KEY" in response["message"]


# Helper Function Tests
def test_persist_task_metadata_success(mock_vector_db):
    """Test successful persistence of task metadata."""
    metadata = {"status": "processing", "task_id": "123"}
    mock_logger = MagicMock()
    persist_task_metadata(mock_vector_db, metadata, logger=mock_logger)
    mock_vector_db.store_task.assert_called_once_with(metadata)
    mock_logger.info.assert_called_once()


def test_persist_task_metadata_failure(mock_vector_db):
    """Test graceful handling of persistence failure."""
    mock_vector_db.store_task.side_effect = Exception("DB Error")
    metadata = {"status": "processing", "task_id": "123"}
    mock_logger = MagicMock()
    persist_task_metadata(
        mock_vector_db, metadata, fallback_status="failed", logger=mock_logger
    )
    mock_vector_db.store_task.assert_called_once_with(metadata)
    assert mock_logger.error.call_count == 2
