import pytest
from unittest.mock import patch, MagicMock

from s3_delete_handler.lambda_function import lambda_handler


@pytest.fixture
def mock_vector_db():
    """Mocks the global vector_db_service instance in the lambda function."""
    with patch("s3_delete_handler.lambda_function.vector_db_service") as mock_service:
        yield mock_service


@pytest.fixture
def mock_is_valid_video():
    """Mocks the is_valid_video_file utility function."""
    with patch("s3_delete_handler.lambda_function.is_valid_video_file") as mock_func:
        yield mock_func


def test_lambda_handler_successful_deletion(
    mock_vector_db, mock_is_valid_video, kubrick_secret, event_builder, test_s3_bucket
):
    """Test successful deletion of a video record from the database."""
    mock_is_valid_video.return_value = True
    mock_vector_db.fetch_video.return_value = [{"id": 1, "filename": "test.mp4"}]
    mock_vector_db.delete_video.return_value = True

    event = event_builder.s3_event(bucket_name=test_s3_bucket, object_key="videos/test.mp4")
    result = lambda_handler(event, {})

    assert result is None
    mock_is_valid_video.assert_called_once_with("videos/test.mp4")
    mock_vector_db.fetch_video.assert_called_once_with(
        bucket=test_s3_bucket, key="videos/test.mp4"
    )
    mock_vector_db.delete_video.assert_called_once_with(
        bucket=test_s3_bucket, key="videos/test.mp4"
    )


def test_lambda_handler_video_not_found_in_db(
    mock_vector_db, mock_is_valid_video, kubrick_secret, event_builder, test_s3_bucket
):
    """Test that delete is not called if the video is not found in the database."""
    mock_is_valid_video.return_value = True
    mock_vector_db.fetch_video.return_value = []  # No records found

    event = event_builder.s3_event(bucket_name=test_s3_bucket, object_key="videos/missing.mp4")
    lambda_handler(event, {})

    mock_vector_db.fetch_video.assert_called_once()
    mock_vector_db.delete_video.assert_not_called()


def test_lambda_handler_invalid_file_extension(
    mock_vector_db, mock_is_valid_video, kubrick_secret, event_builder, test_s3_bucket
):
    """Test that no database operations occur for non-video files."""
    mock_is_valid_video.return_value = False

    event = event_builder.s3_event(bucket_name=test_s3_bucket, object_key="docs/readme.txt")
    lambda_handler(event, {})

    mock_is_valid_video.assert_called_once_with("docs/readme.txt")
    mock_vector_db.fetch_video.assert_not_called()
    mock_vector_db.delete_video.assert_not_called()


def test_lambda_handler_delete_failure_in_db(
    mock_vector_db, mock_is_valid_video, kubrick_secret, event_builder, test_s3_bucket
):
    """Test graceful handling when the database delete operation fails."""
    mock_is_valid_video.return_value = True
    mock_vector_db.fetch_video.return_value = [{"id": 1}]
    mock_vector_db.delete_video.return_value = False  # Simulate failure

    event = event_builder.s3_event(bucket_name=test_s3_bucket, object_key="videos/test.mp4")
    lambda_handler(event, {})

    mock_vector_db.fetch_video.assert_called_once()
    mock_vector_db.delete_video.assert_called_once()


def test_lambda_handler_multiple_records(
    mock_vector_db, mock_is_valid_video, kubrick_secret, event_builder, test_s3_bucket
):
    """Test processing of an S3 event with multiple records, some valid, some not."""
    mock_is_valid_video.side_effect = [True, False, True]
    mock_vector_db.fetch_video.side_effect = [[{"id": 1}], [{"id": 2}]]
    mock_vector_db.delete_video.return_value = True

    event = {
        "Records": [
            event_builder.s3_event(test_s3_bucket, "videos/video1.mp4")["Records"][0],
            event_builder.s3_event(test_s3_bucket, "docs/file.txt")["Records"][0],
            event_builder.s3_event(test_s3_bucket, "videos/video3.mov")["Records"][0],
        ]
    }
    lambda_handler(event, {})

    assert mock_is_valid_video.call_count == 3
    assert mock_vector_db.fetch_video.call_count == 2
    assert mock_vector_db.delete_video.call_count == 2


def test_lambda_handler_url_encoded_key(
    mock_vector_db, mock_is_valid_video, kubrick_secret, event_builder, test_s3_bucket
):
    """Test that URL-encoded S3 keys are properly decoded."""
    mock_is_valid_video.return_value = True
    mock_vector_db.fetch_video.return_value = [{"id": 1}]
    mock_vector_db.delete_video.return_value = True

    encoded_key = "videos/my%20video%20file%281%29.mp4"
    decoded_key = "videos/my video file(1).mp4"
    event = event_builder.s3_event(bucket_name=test_s3_bucket, object_key=encoded_key)
    lambda_handler(event, {})

    mock_is_valid_video.assert_called_once_with(decoded_key)
    mock_vector_db.fetch_video.assert_called_once_with(
        bucket=test_s3_bucket, key=decoded_key
    )


def test_lambda_handler_database_exception(
    mock_vector_db, mock_is_valid_video, kubrick_secret, event_builder, test_s3_bucket
):
    """Test that the handler gracefully exits when the database throws an exception."""
    mock_is_valid_video.return_value = True
    mock_vector_db.fetch_video.side_effect = Exception("Database connection failed")

    event = event_builder.s3_event(bucket_name=test_s3_bucket, object_key="videos/test.mp4")
    result = lambda_handler(event, {})

    assert result is None
    mock_vector_db.fetch_video.assert_called_once()
    mock_vector_db.delete_video.assert_not_called()


