import sys
import os
import pytest
import json
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3

# Path to layers
layers_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../layers"))
sys.path.insert(0, os.path.join(layers_dir, "embed_service_layer"))
sys.path.insert(0, os.path.join(layers_dir, "vector_database_layer"))
sys.path.insert(0, os.path.join(layers_dir, "s3_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "config_layer"))

# Lambda handler path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../sqs_embedding_task_consumer")))

mock_aws_instance = mock_aws()
mock_aws_instance.start()

from lambda_function import lambda_handler, get_video_metadata
from twelvelabs.types import VideoEmbeddingMetadata, VideoSegment

mock_aws_instance.stop()

class TestLambdaHandler:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.moto_mock = mock_aws()
        self.moto_mock.start()

        # Re-create the secret for each test to ensure isolation
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = {
            "TWELVELABS_API_KEY": "test_twelvelabs_api_key",
            "DB_USERNAME": "test_db_user",
            "DB_PASSWORD": "test_db_password",
            "DB_HOST": "test_db_host",
            "DB_NAME": "test_db_name",
            "DB_PORT": "5432"
        }
        try:
            secretsmanager.create_secret(
                Name="kubrick_secret",
                SecretString=json.dumps(secret_value)
            )
        except secretsmanager.exceptions.ResourceExistsException:
            # If the secret already exists (e.g., from a previous test run in the same session), update it
            secretsmanager.update_secret(
                SecretId="kubrick_secret",
                SecretString=json.dumps(secret_value)
            )

        # Mock dependencies for the handler
        self.mock_setup_logging = patch('lambda_function.setup_logging').start()
        self.mock_get_secret = patch('lambda_function.get_secret').start()
        self.mock_get_db_config = patch('lambda_function.get_db_config').start()
        self.mock_embed_service = patch('lambda_function.EmbedService').start()
        self.mock_vector_db_service = patch('lambda_function.VectorDBService').start()
        self.mock_os_path_basename = patch('os.path.basename').start()


        # Configure mocks with default return values
        self.mock_logger_instance = MagicMock()
        self.mock_setup_logging.return_value = self.mock_logger_instance
        self.mock_get_secret.return_value = secret_value
        self.mock_get_db_config.return_value = {
            "host": "localhost", "database": "kubrick", "user": "postgres", "password": "password", "port": 5432
        }

        self.mock_embed_service_instance = MagicMock()
        self.mock_embed_service.return_value = self.mock_embed_service_instance

        self.mock_vector_db_service_instance = MagicMock()
        self.mock_vector_db_service.return_value = self.mock_vector_db_service_instance

        self.mock_os_path_basename.return_value = "test_video.mp4"

        yield # Run the test

        # Stop moto mock and unpatch for each test
        patch.stopall()
        self.moto_mock.stop()


    def create_sqs_event_record(self, message_id, s3_bucket, s3_key, tl_task_id=None):
        """Helper to create a single SQS event record."""
        body = {
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
        }
        if tl_task_id:
            body["twelvelabs_video_embedding_task_id"] = tl_task_id

        return {
            "messageId": message_id,
            "receiptHandle": f"receipt-handle-{message_id}",
            "body": json.dumps(body),
            "attributes": {},
            "messageAttributes": {},
            "md5OfBody": "",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:test-queue",
            "awsRegion": "us-east-1"
        }

    def test_lambda_handler_success_ready_status(self):
        """Test successful processing when TwelveLabs task is 'ready'."""
        mock_task_id = "tl-task-123"
        message_id = "msg-1"
        s3_bucket = "test-bucket"
        s3_key = "videos/test_video.mp4"

        event = {
            "Records": [
                self.create_sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)
            ]
        }
        context = MagicMock()

        # Mock embed_service behavior for 'ready' status
        self.mock_embed_service_instance.get_embedding_request_status.return_value = "ready"

        mock_tl_response = MagicMock()
        mock_tl_response.video_embedding.segments = [
            MagicMock(
                start_offset_sec=0, end_offset_sec=5, embedding_scope="clip",
                embedding_option="text-visual", float_=[0.1, 0.2]
            ),
            MagicMock(
                start_offset_sec=0, end_offset_sec=10, embedding_scope="video",
                embedding_option="text-visual", float_=[0.3, 0.4]
            ),
        ]
        mock_tl_response.video_embedding.metadata = MagicMock(duration=120)
        self.mock_embed_service_instance.retrieve_embed_response.return_value = mock_tl_response
        self.mock_embed_service_instance.get_video_metadata.return_value = MagicMock(duration=120)

        # Expected normalized segments based on normalize_segments in embed_service.py
        expected_normalized_segments = [
            {"start_time": 0, "end_time": 5, "scope": "clip", "modality": "text-visual", "embedding": [0.1, 0.2]},
            {"start_time": 0, "end_time": 10, "scope": "video", "modality": "text-visual", "embedding": [0.3, 0.4]},
        ]
        self.mock_embed_service_instance.normalize_segments.return_value = expected_normalized_segments

        response = lambda_handler(event, context)

        # Assertions
        self.mock_embed_service_instance.get_embedding_request_status.assert_called_once_with(mock_task_id)
        self.mock_embed_service_instance.retrieve_embed_response.assert_called_once_with(task_id=mock_task_id)
        self.mock_embed_service_instance.get_video_metadata.assert_called_once_with(response=mock_tl_response)
        self.mock_os_path_basename.assert_called_once_with(s3_key)
        self.mock_embed_service_instance.normalize_segments.assert_called_once_with(mock_tl_response.video_embedding.segments)

        expected_video_metadata = {
            "filename": "test_video.mp4",
            "duration": 120,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
        }
        self.mock_vector_db_service_instance.store.assert_called_once_with(expected_video_metadata, expected_normalized_segments)
        self.mock_vector_db_service_instance.update_task_status.assert_called_once_with(message_id, "completed")
        self.mock_logger_instance.info.assert_any_call("Successfully stored video and segments in DB")
        self.mock_logger_instance.info.assert_any_call("Successfully updated task status in DB")
        assert response == {}

    def test_lambda_handler_failed_status(self):
        """Test processing when TwelveLabs task is 'failed'."""
        mock_task_id = "tl-task-456"
        message_id = "msg-2"
        s3_bucket = "test-bucket"
        s3_key = "videos/another_video.mp4"

        event = {
            "Records": [
                self.create_sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)
            ]
        }
        context = MagicMock()

        self.mock_embed_service_instance.get_embedding_request_status.return_value = "failed"

        response = lambda_handler(event, context)

        # Assertions
        self.mock_embed_service_instance.get_embedding_request_status.assert_called_once_with(mock_task_id)
        self.mock_vector_db_service_instance.update_task_status.assert_called_once_with(message_id, "failed")
        self.mock_logger_instance.error.assert_called_once() # Should log the failure
        self.mock_logger_instance.info.assert_any_call("Successfully updated task status in DB")
        assert response == {}

    def test_lambda_handler_processing_status(self):
        """Test processing when TwelveLabs task is 'processing' (re-queues message)."""
        mock_task_id = "tl-task-789"
        message_id = "msg-3"
        s3_bucket = "test-bucket"
        s3_key = "videos/yet_another_video.mp4"

        event = {
            "Records": [
                self.create_sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)
            ]
        }
        context = MagicMock()

        self.mock_embed_service_instance.get_embedding_request_status.return_value = "processing"

        response = lambda_handler(event, context)

        # Assertions
        self.mock_embed_service_instance.get_embedding_request_status.assert_called_once_with(mock_task_id)
        self.mock_vector_db_service_instance.update_task_status.assert_called_once_with(message_id, "processing")
        self.mock_logger_instance.info.assert_any_call(f"TwelveLabs video embedding task {mock_task_id} is still processing. Re-queueing.")
        self.mock_logger_instance.info.assert_any_call("Successfully updated task status in DB")
        assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}

    def test_lambda_handler_general_exception(self):
        """Test handling a general exception during message processing."""
        mock_task_id = "tl-task-101"
        message_id = "msg-4"
        s3_bucket = "test-bucket"
        s3_key = "videos/error_video.mp4"

        event = {
            "Records": [
                self.create_sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)
            ]
        }
        context = MagicMock()

        # Simulate an exception when getting task status
        self.mock_embed_service_instance.get_embedding_request_status.side_effect = Exception("API connection error")

        response = lambda_handler(event, context)

        # Assertions
        self.mock_logger_instance.error.assert_called_once_with(f"Error processing task {message_id}: API connection error")
        self.mock_vector_db_service_instance.update_task_status.assert_called_once_with(message_id, "retrying")
        self.mock_logger_instance.info.assert_any_call("Successfully updated task status in DB")
        assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}

    def test_lambda_handler_multiple_records(self):
        """Test handling multiple SQS records with different statuses."""
        event = {
            "Records": [
                self.create_sqs_event_record("msg-10", "bucket", "key1.mp4", "tl-10", ), # Ready
                self.create_sqs_event_record("msg-11", "bucket", "key2.mp4", "tl-11", ), # Failed
                self.create_sqs_event_record("msg-12", "bucket", "key3.mp4", "tl-12", ), # Processing
                self.create_sqs_event_record("msg-13", "bucket", "key4.mp4", "tl-13", ), # Error
            ]
        }
        context = MagicMock()

        self.mock_embed_service_instance.get_embedding_request_status.side_effect = [
            "ready", # msg-10
            "failed", # msg-11
            "processing", # msg-12
            Exception("Simulated error for msg-13"), # msg-13
        ]

        # Mocks for the 'ready' task (msg-10)
        mock_tl_response_ready = MagicMock()
        mock_tl_response_ready.video_embedding.segments = [
            MagicMock(start_offset_sec=0, end_offset_sec=10, embedding_scope="video", embedding_option="text-visual", float_=[0.5, 0.6])
        ]
        mock_tl_response_ready.video_embedding.metadata = MagicMock(duration=90)
        self.mock_embed_service_instance.retrieve_embed_response.return_value = mock_tl_response_ready
        self.mock_embed_service_instance.get_video_metadata.return_value = MagicMock(duration=90)
        self.mock_embed_service_instance.normalize_segments.return_value = [
            {"start_time": 0, "end_time": 90, "scope": "video", "modality": "text-visual", "embedding": [0.5, 0.6]}
        ]

        response = lambda_handler(event, context)

        # Assertions for each message
        # msg-10 (ready)
        self.mock_embed_service_instance.get_embedding_request_status.assert_any_call("tl-10")
        self.mock_vector_db_service_instance.update_task_status.assert_any_call("msg-10", "completed")

        # msg-11 (failed)
        self.mock_embed_service_instance.get_embedding_request_status.assert_any_call("tl-11")
        self.mock_vector_db_service_instance.update_task_status.assert_any_call("msg-11", "failed")

        # msg-12 (processing)
        self.mock_embed_service_instance.get_embedding_request_status.assert_any_call("tl-12")
        self.mock_vector_db_service_instance.update_task_status.assert_any_call("msg-12", "processing")

        # msg-13 (error)
        self.mock_embed_service_instance.get_embedding_request_status.assert_any_call("tl-13")
        self.mock_vector_db_service_instance.update_task_status.assert_any_call("msg-13", "retrying")

        # Verify batchItemFailures contains messages that failed or are still processing
        assert len(response["batchItemFailures"]) == 2
        assert {"itemIdentifier": "msg-12"} in response["batchItemFailures"]
        assert {"itemIdentifier": "msg-13"} in response["batchItemFailures"]

    def test_lambda_handler_empty_records(self):
        """Test handler with an empty 'Records' list."""
        event = {"Records": []}
        context = MagicMock()

        response = lambda_handler(event, context)

        # No processing should happen, services should not be called
        self.mock_embed_service_instance.get_embedding_request_status.assert_not_called()
        self.mock_vector_db_service_instance.update_task_status.assert_not_called()
        assert response == {}

    def test_lambda_handler_malformed_message_body(self):
        """Test handling of a malformed SQS message body (json.loads fails)."""
        message_id = "msg-malformed"
        event = {
            "Records": [
                {
                    "messageId": message_id,
                    "receiptHandle": f"receipt-handle-{message_id}",
                    "body": "{invalid json", # Malformed JSON
                    "attributes": {}, "messageAttributes": {}, "md5OfBody": "",
                    "eventSource": "aws:sqs", "eventSourceARN": "", "awsRegion": "us-east-1"
                }
            ]
        }
        context = MagicMock()

        response = lambda_handler(event, context)

        self.mock_logger_instance.error.assert_called_once() # Should log the JSON decoding error
        self.mock_vector_db_service_instance.update_task_status.assert_called_once_with(message_id, "retrying")
        assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}

    def test_lambda_handler_get_video_metadata_none_tl_metadata(self):
        """Test get_video_metadata helper when tl_metadata is None."""
        message_body = {"s3_bucket": "test-bucket", "s3_key": "videos/no_metadata.mp4"}
        self.mock_os_path_basename.return_value = "no_metadata.mp4"

        metadata = get_video_metadata(None, message_body)

        assert metadata == {
            "filename": "no_metadata.mp4",
            "s3_bucket": "test-bucket",
            "s3_key": "videos/no_metadata.mp4",
        }
        assert "duration" not in metadata

    def test_lambda_handler_retrieve_embed_response_no_embedding_segments(self):
        """Test scenario where retrieve_embed_response returns no video_embedding or segments."""
        mock_task_id = "tl-task-no-embed"
        message_id = "msg-no-embed"
        s3_bucket = "test-bucket"
        s3_key = "videos/no_embedding.mp4"

        event = {
            "Records": [
                self.create_sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)
            ]
        }
        context = MagicMock()

        self.mock_embed_service_instance.get_embedding_request_status.return_value = "ready"
        # Simulate a response missing video_embedding or segments
        mock_tl_response_no_embed = MagicMock()
        mock_tl_response_no_embed.video_embedding = None # This causes AttributeError in lambda_function.py
        self.mock_embed_service_instance.retrieve_embed_response.return_value = mock_tl_response_no_embed

        response = lambda_handler(event, context)

        # Expect an error and message to be re-queued
        # Updated assertion to match the actual AttributeError message
        self.mock_logger_instance.error.assert_called_once_with(f"Error processing task {message_id}: 'NoneType' object has no attribute 'segments'")
        self.mock_vector_db_service_instance.update_task_status.assert_called_once_with(message_id, "retrying")
        assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}


    def test_lambda_handler_db_store_failure(self):
        """Test scenario where vector_db_service.store fails."""
        mock_task_id = "tl-task-db-fail"
        message_id = "msg-db-fail"
        s3_bucket = "test-bucket"
        s3_key = "videos/db_fail_video.mp4"

        event = {
            "Records": [
                self.create_sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)
            ]
        }
        context = MagicMock()

        self.mock_embed_service_instance.get_embedding_request_status.return_value = "ready"

        mock_tl_response = MagicMock()
        mock_tl_response.video_embedding.segments = [
            MagicMock(start_offset_sec=0, end_offset_sec=5, embedding_scope="clip", embedding_option="text-visual", float_=[0.1, 0.2])
        ]
        mock_tl_response.video_embedding.metadata = MagicMock(duration=120)
        self.mock_embed_service_instance.retrieve_embed_response.return_value = mock_tl_response
        self.mock_embed_service_instance.get_video_metadata.return_value = MagicMock(duration=120)
        self.mock_embed_service_instance.normalize_segments.return_value = [
            {"start_time": 0, "end_time": 5, "scope": "clip", "modality": "text-visual", "embedding": [0.1, 0.2]}
        ]

        # Simulate database store failure
        self.mock_vector_db_service_instance.store.side_effect = Exception("Database write error")

        response = lambda_handler(event, context)

        # The message should be re-queued because the store failed
        self.mock_logger_instance.error.assert_called_once_with(f"Error processing task {message_id}: Database write error")
        self.mock_vector_db_service_instance.update_task_status.assert_called_once_with(message_id, "retrying")
        assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}

    def test_lambda_handler_db_update_task_status_failure(self):
        """Test scenario where vector_db_service.update_task_status fails."""
        mock_task_id = "tl-task-update-fail"
        message_id = "msg-update-fail"
        s3_bucket = "test-bucket"
        s3_key = "videos/update_fail_video.mp4"

        event = {
            "Records": [
                self.create_sqs_event_record(message_id, s3_bucket, s3_key, mock_task_id)
            ]
        }
        context = MagicMock()

        self.mock_embed_service_instance.get_embedding_request_status.return_value = "ready"

        mock_tl_response = MagicMock()
        mock_tl_response.video_embedding.segments = [
            MagicMock(start_offset_sec=0, end_offset_sec=5, embedding_scope="clip", embedding_option="text-visual", float_=[0.1, 0.2])
        ]
        mock_tl_response.video_embedding.metadata = MagicMock(duration=120)
        self.mock_embed_service_instance.retrieve_embed_response.return_value = mock_tl_response
        self.mock_embed_service_instance.get_video_metadata.return_value = MagicMock(duration=120)
        self.mock_embed_service_instance.normalize_segments.return_value = [
            {"start_time": 0, "end_time": 5, "scope": "clip", "modality": "text-visual", "embedding": [0.1, 0.2]}
        ]

        # Simulate update_task_status failure after successful store
        # First call (completed) fails, second call (retrying) succeeds
        self.mock_vector_db_service_instance.update_task_status.side_effect = [Exception("Database update error"), None]

        response = lambda_handler(event, context)

        # Verify the logger was called with the error and the update_task_status was called for retrying
        self.mock_logger_instance.error.assert_called_once_with(f"Error processing task {message_id}: Database update error")
        self.mock_vector_db_service_instance.update_task_status.assert_called_with(message_id, "retrying") # Last call should be 'retrying'
        assert response == {"batchItemFailures": [{"itemIdentifier": message_id}]}
