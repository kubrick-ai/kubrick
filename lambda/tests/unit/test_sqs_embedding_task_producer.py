import sys
import os
import boto3
import json
from moto import mock_aws
from unittest.mock import patch, MagicMock


# Mock external dependencies completely
sys.modules["twelvelabs"] = MagicMock()
sys.modules["embed_service"] = MagicMock()

# Path to layers
layers_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/layers")
)
sys.path.insert(0, os.path.join(layers_dir, "response_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "vector_database_layer"))
sys.path.insert(0, os.path.join(layers_dir, "s3_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "config_layer"))

# Lambda handler path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/")),
)

with patch.dict("os.environ", {"QUEUE_URL": "https://test-queue-url"}):
    from sqs_embedding_task_producer import lambda_function


class TestSQSEmbeddingTaskProducer:

    @mock_aws
    @patch("sqs_embedding_task_producer.lambda_function.EmbedService")
    @patch("sqs_embedding_task_producer.lambda_function.VectorDBService")
    @patch("sqs_embedding_task_producer.lambda_function.s3_utils.wait_for_file")
    @patch(
        "sqs_embedding_task_producer.lambda_function.s3_utils.generate_presigned_url"
    )
    def test_lambda_handler_success(
        self,
        mock_generate_presigned_url,
        mock_wait_for_file,
        mock_vector_db_service,
        mock_embed_service,
    ):
        # Setup mocks
        mock_embed_service_instance = MagicMock()
        mock_embedding_response = MagicMock()
        mock_embedding_response.id = "test-task-id-123"
        mock_embed_service_instance.create_embedding_request.return_value = (
            mock_embedding_response
        )
        mock_embed_service.return_value = mock_embed_service_instance

        mock_vector_db = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db

        mock_wait_for_file.return_value = True
        mock_generate_presigned_url.return_value = "https://presigned-url.com/video.mp4"

        # Setup AWS services
        sqs = boto3.client("sqs", region_name="us-east-1")
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = {
            "DB_USERNAME": "test_user",
            "DB_PASSWORD": "test_pass",
            "TWELVELABS_API_KEY": "test_api_key",
        }
        secretsmanager.create_secret(
            Name="kubrick_secret", SecretString=json.dumps(secret_value)
        )

        # Test S3 event
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "videos/test-video.mp4"},
                    }
                }
            ]
        }
        context = {}

        # Execute with proper environment
        with patch.dict(
            "os.environ", {"AWS_DEFAULT_REGION": "us-east-1", "QUEUE_URL": queue_url}
        ), patch("sqs_embedding_task_producer.lambda_function.QUEUE_URL", queue_url):
            response = lambda_function.lambda_handler(event, context)

        # Assertions
        assert response["status"] == "success"
        assert response["task_id"] == "test-task-id-123"
        assert "sqs_message_id" in response
        assert response["s3_bucket"] == "test-bucket"
        assert response["s3_key"] == "videos/test-video.mp4"

        # Verify service calls
        mock_embed_service_instance.create_embedding_request.assert_called_once_with(
            url="https://presigned-url.com/video.mp4"
        )
        mock_vector_db.store_task.assert_called_once()

    @mock_aws
    @patch("sqs_embedding_task_producer.lambda_function.EmbedService")
    @patch("sqs_embedding_task_producer.lambda_function.VectorDBService")
    def test_lambda_handler_folder_event_ignored(
        self, mock_vector_db_service, mock_embed_service
    ):
        # Setup minimal mocks
        mock_vector_db = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = {"TWELVELABS_API_KEY": "test_api_key"}
        secretsmanager.create_secret(
            Name="kubrick_secret", SecretString=json.dumps(secret_value)
        )

        # Test S3 folder creation event
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "videos/"},
                    }
                }
            ]
        }
        context = {}

        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
            response = lambda_function.lambda_handler(event, context)

        assert response["status"] == "ignored"
        assert response["reason"] == "S3 event is a folder creation"

    @mock_aws
    @patch("sqs_embedding_task_producer.lambda_function.EmbedService")
    @patch("sqs_embedding_task_producer.lambda_function.VectorDBService")
    @patch("sqs_embedding_task_producer.lambda_function.utils.is_valid_video_file")
    def test_lambda_handler_invalid_video_file(
        self, mock_is_valid_video_file, mock_vector_db_service, mock_embed_service
    ):
        # Setup mocks
        mock_vector_db = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db
        mock_is_valid_video_file.return_value = False

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = {"TWELVELABS_API_KEY": "test_api_key"}
        secretsmanager.create_secret(
            Name="kubrick_secret", SecretString=json.dumps(secret_value)
        )

        # Test S3 event with invalid file
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "documents/text-file.txt"},
                    }
                }
            ]
        }
        context = {}

        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
            response = lambda_function.lambda_handler(event, context)

        assert response["status"] == "error"
        assert (
            "not a video" in response["message"]
            or "not supported" in response["message"]
        )

        # Verify task metadata was stored with failed status
        mock_vector_db.store_task.assert_called_once()
        stored_metadata = mock_vector_db.store_task.call_args[0][0]
        assert stored_metadata["status"] == "failed"

    @mock_aws
    @patch("sqs_embedding_task_producer.lambda_function.EmbedService")
    @patch("sqs_embedding_task_producer.lambda_function.VectorDBService")
    @patch("sqs_embedding_task_producer.lambda_function.s3_utils.wait_for_file")
    def test_lambda_handler_file_not_found(
        self, mock_wait_for_file, mock_vector_db_service, mock_embed_service
    ):
        # Setup mocks
        mock_vector_db = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db
        mock_wait_for_file.return_value = False

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = {"TWELVELABS_API_KEY": "test_api_key"}
        secretsmanager.create_secret(
            Name="kubrick_secret", SecretString=json.dumps(secret_value)
        )

        # Test S3 event
        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "videos/missing-video.mp4"},
                    }
                }
            ]
        }
        context = {}

        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
            response = lambda_function.lambda_handler(event, context)

        assert response["status"] == "error"
        assert "not found" in response["message"]

        # Verify task metadata was stored with failed status
        mock_vector_db.store_task.assert_called_once()
        stored_metadata = mock_vector_db.store_task.call_args[0][0]
        assert stored_metadata["status"] == "failed"
