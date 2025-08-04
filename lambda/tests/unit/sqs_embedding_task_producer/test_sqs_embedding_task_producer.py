import sys
import os
import pytest
import boto3
import json
from moto import mock_aws
from unittest.mock import patch, MagicMock

# Path to layers
layers_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../layers"))
sys.path.insert(0, os.path.join(layers_dir, "embed_service_layer"))
sys.path.insert(0, os.path.join(layers_dir, "vector_database_layer"))
sys.path.insert(0, os.path.join(layers_dir, "s3_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "config_layer"))

# Lambda handler path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../sqs_embedding_task_producer")))

# Setup AWS mocking and required environment variables before importing lambda_function
mock_aws_instance = mock_aws()
mock_aws_instance.start()

# Set up environment variables
os.environ['QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Create the secret that the module expects at import time
secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
secret_value = {
    "TWELVELABS_API_KEY": "test_import_key",
    "DB_USERNAME": "test_user",
    "DB_PASSWORD": "test_pass"
}
secretsmanager.create_secret(
    Name="kubrick_secret",
    SecretString=json.dumps(secret_value)
)

# Import lambda
from lambda_function import lambda_handler, persist_task_metadata

# Clean up the global mock (individual tests will set up their own)
mock_aws_instance.stop()


class TestLambdaHandler:
    
    def create_s3_event(self, bucket_name, object_key, event_name="ObjectCreated:Put"):
        """Helper to create S3 event for testing"""
        return {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": "us-east-1",
                    "eventTime": "2023-01-01T00:00:00.000Z",
                    "eventName": event_name,
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "bucket": {
                            "name": bucket_name,
                            "arn": f"arn:aws:s3:::{bucket_name}"
                        },
                        "object": {
                            "key": object_key,
                            "size": 1024
                        }
                    }
                }
            ]
        }

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    @patch('s3_utils.wait_for_file')
    @patch('s3_utils.generate_presigned_url')
    def test_lambda_handler_success_mp4_file(
        self, 
        mock_presigned_url, 
        mock_wait_for_file, 
        mock_vector_db_service, 
        mock_embed_service
    ):
        """Test successful processing of MP4 video file"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        s3 = boto3.client("s3", region_name="us-east-1")
        
        secret_value = {
            "TWELVELABS_API_KEY": "test_api_key_12345",
            "DB_USERNAME": "test_user",
            "DB_PASSWORD": "test_pass"
        }
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps(secret_value)
        )
        
        # Create SQS queue
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]
        
        # Create S3 bucket
        s3.create_bucket(Bucket="test-bucket")
        
        mock_embed_task = MagicMock()
        mock_embed_task.id = 12345
        mock_embed_service_instance = MagicMock()
        mock_embed_service_instance.create_embedding_request.return_value = mock_embed_task
        mock_embed_service.return_value = mock_embed_service_instance
        
        mock_vector_db_instance = MagicMock()
        mock_vector_db_instance.store_task.return_value = None
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        mock_wait_for_file.return_value = True
        mock_presigned_url.return_value = "https://test-presigned-url.com"
        
        event = self.create_s3_event("test-bucket", "videos/test_video.mp4")
        context = {}
        
        with patch.dict('os.environ', {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'QUEUE_URL': queue_url
        }):
            response = lambda_handler(event, context)
        
        # Assertions
        assert response["status"] == "success"
        assert response["task_id"] == 12345
        assert response["s3_bucket"] == "test-bucket"
        assert response["s3_key"] == "videos/test_video.mp4"
        assert "sqs_message_id" in response
        
        mock_embed_service.assert_called_once()
        mock_embed_service_instance.create_embedding_request.assert_called_once()
        mock_vector_db_instance.store_task.assert_called_once()
        
        # Check wait_for_file call (logger is positional argument)
        wait_for_file_call_args = mock_wait_for_file.call_args
        assert wait_for_file_call_args[0][:4] == ("test-bucket", "videos/test_video.mp4", 2, 2.0)
        
        mock_presigned_url.assert_called_once_with(
            bucket="test-bucket", 
            key="videos/test_video.mp4", 
            expires_in=600
        )

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    @patch('s3_utils.wait_for_file')
    @patch('s3_utils.generate_presigned_url')
    def test_lambda_handler_success_various_video_formats(
        self, 
        mock_presigned_url, 
        mock_wait_for_file, 
        mock_vector_db_service, 
        mock_embed_service
    ):
        """Test successful processing of various video file formats"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test_key"})
        )
        
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]

        mock_embed_task = MagicMock()
        mock_embed_task.id = 54321
        mock_embed_service_instance = MagicMock()
        mock_embed_service_instance.create_embedding_request.return_value = mock_embed_task
        mock_embed_service.return_value = mock_embed_service_instance
        
        mock_vector_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        mock_wait_for_file.return_value = True
        mock_presigned_url.return_value = "https://test-presigned-url.com"
        
        # Test various video formats
        video_formats = [
            "test_video.mov",
            "test_video.avi", 
            "test_video.mkv",
            "test_video.webm",
            "test_video.flv",
            "test_video.wmv",
            "test_video.m4v"
        ]
        
        for video_file in video_formats:
            event = self.create_s3_event("test-bucket", f"videos/{video_file}")
            context = {}
            
            with patch.dict('os.environ', {
                'AWS_DEFAULT_REGION': 'us-east-1',
                'QUEUE_URL': queue_url
            }):
                response = lambda_handler(event, context)
            
            assert response["status"] == "success"
            assert response["s3_key"] == f"videos/{video_file}"

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    def test_lambda_handler_invalid_file_type(self, mock_vector_db_service, mock_embed_service):
        """Test handling of invalid file types (non-video files)"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test_key"})
        )
        
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]
        
        mock_vector_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        invalid_files = [
            "document.pdf",
            "image.jpg", 
            "audio.mp3",
            "text.txt",
            "archive.zip"
        ]
        
        for invalid_file in invalid_files:
            event = self.create_s3_event("test-bucket", f"uploads/{invalid_file}")
            context = {}
            
            with patch.dict('os.environ', {
                'AWS_DEFAULT_REGION': 'us-east-1',
                'QUEUE_URL': queue_url
            }):
                response = lambda_handler(event, context)
            
            assert response["status"] == "error"
            assert "not a video or the video format is not supported" in response["message"]
            
            # Verify task metadata was stored with failed status
            mock_vector_db_instance.store_task.assert_called()

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    def test_lambda_handler_folder_creation_event(self, mock_vector_db_service, mock_embed_service):
        """Test handling of S3 folder creation events (should be ignored)"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test_key"})
        )
        
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]
        
        # Create S3 event for folder creation
        event = self.create_s3_event("test-bucket", "videos/")
        context = {}
        
        with patch.dict('os.environ', {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'QUEUE_URL': queue_url
        }):
            response = lambda_handler(event, context)
        
        assert response["status"] == "ignored"
        assert response["reason"] == "S3 event is a folder creation"
        
        # Verify services were not called for processing
        mock_embed_service.assert_called_once()  # Service is initialized but not used
        mock_vector_db_service.assert_called_once()  # Service is initialized but not used

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    @patch('s3_utils.wait_for_file')
    def test_lambda_handler_file_not_found(self, mock_wait_for_file, mock_vector_db_service, mock_embed_service):
        """Test handling of S3 file not found after retries"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test_key"})
        )
        
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]
        
        mock_vector_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        mock_wait_for_file.return_value = False  # File not found
        
        event = self.create_s3_event("test-bucket", "videos/missing_video.mp4")
        context = {}
        
        with patch.dict('os.environ', {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'QUEUE_URL': queue_url
        }):
            response = lambda_handler(event, context)
        
        assert response["status"] == "error"
        assert "not found after retries" in response["message"]
        
        mock_vector_db_instance.store_task.assert_called()

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    @patch('s3_utils.wait_for_file')
    @patch('s3_utils.generate_presigned_url')
    def test_lambda_handler_embed_service_failure(
        self, 
        mock_presigned_url, 
        mock_wait_for_file, 
        mock_vector_db_service, 
        mock_embed_service
    ):
        """Test handling of EmbedService create_embedding_request failure"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test_key"})
        )
        
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]
        
        # Mock services
        mock_embed_service_instance = MagicMock()
        mock_embed_service_instance.create_embedding_request.side_effect = Exception("TwelveLabs API error")
        mock_embed_service.return_value = mock_embed_service_instance
        
        mock_vector_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        mock_wait_for_file.return_value = True
        mock_presigned_url.return_value = "https://test-presigned-url.com"
        
        event = self.create_s3_event("test-bucket", "videos/test_video.mp4")
        context = {}
        
        with patch.dict('os.environ', {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'QUEUE_URL': queue_url
        }):
            response = lambda_handler(event, context)
        
        assert response["status"] == "error"
        assert "TwelveLabs API error" in response["message"]
        
        # Verify task metadata was stored with failed status
        mock_vector_db_instance.store_task.assert_called()

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    @patch('s3_utils.wait_for_file')
    @patch('s3_utils.generate_presigned_url')
    def test_lambda_handler_sqs_send_message_failure(
        self, 
        mock_presigned_url, 
        mock_wait_for_file, 
        mock_vector_db_service, 
        mock_embed_service
    ):
        """Test handling of SQS send message failure"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test_key"})
        )
        
        mock_embed_task = MagicMock()
        mock_embed_task.id = 12345
        mock_embed_service_instance = MagicMock()
        mock_embed_service_instance.create_embedding_request.return_value = mock_embed_task
        mock_embed_service.return_value = mock_embed_service_instance
        
        mock_vector_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        mock_wait_for_file.return_value = True
        mock_presigned_url.return_value = "https://test-presigned-url.com"
        
        event = self.create_s3_event("test-bucket", "videos/test_video.mp4")
        context = {}
        
        # Use invalid queue URL to trigger SQS error
        with patch.dict('os.environ', {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/nonexistent-queue'
        }):
            response = lambda_handler(event, context)
        
        assert response["status"] == "error"
        
        # Verify task metadata was stored with failed status
        mock_vector_db_instance.store_task.assert_called()

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    @patch('s3_utils.wait_for_file')
    @patch('s3_utils.generate_presigned_url')
    def test_lambda_handler_database_store_task_failure(
        self, 
        mock_presigned_url, 
        mock_wait_for_file, 
        mock_vector_db_service, 
        mock_embed_service
    ):
        """Test handling when database task storage fails"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test_key"})
        )
        
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]
        
        # Mock services
        mock_embed_task = MagicMock()
        mock_embed_task.id = 12345
        mock_embed_service_instance = MagicMock()
        mock_embed_service_instance.create_embedding_request.return_value = mock_embed_task
        mock_embed_service.return_value = mock_embed_service_instance
        
        mock_vector_db_instance = MagicMock()
        mock_vector_db_instance.store_task.side_effect = Exception("Database connection failed")
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        mock_wait_for_file.return_value = True
        mock_presigned_url.return_value = "https://test-presigned-url.com"
        
        event = self.create_s3_event("test-bucket", "videos/test_video.mp4")
        context = {}
        
        with patch.dict('os.environ', {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'QUEUE_URL': queue_url
        }):
            response = lambda_handler(event, context)
        
        # Even if database storage fails, the lambda should still succeed if other operations work
        assert response["status"] == "success"
        assert response["task_id"] == 12345

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    def test_lambda_handler_missing_s3_records(self, mock_vector_db_service, mock_embed_service):
        """Test handling of malformed S3 event (missing Records)"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test_key"})
        )
        
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]
        
        mock_vector_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        # Event without Records
        event = {"someOtherField": "value"}
        context = {}
        
        with patch.dict('os.environ', {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'QUEUE_URL': queue_url
        }):
            response = lambda_handler(event, context)
        
        assert response["status"] == "error"
        assert "No Records found in event" in response["message"]

    @mock_aws
    @patch('lambda_function.EmbedService')
    @patch('lambda_function.VectorDBService')
    def test_lambda_handler_malformed_s3_record(self, mock_vector_db_service, mock_embed_service):
        """Test handling of malformed S3 record (missing bucket or key)"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test_key"})
        )
        
        queue_response = sqs.create_queue(QueueName="test-queue")
        queue_url = queue_response["QueueUrl"]
        
        mock_vector_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        # Event with malformed record (missing s3 info)
        event = {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": "us-east-1"
                }
            ]
        }
        context = {}
        
        with patch.dict('os.environ', {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'QUEUE_URL': queue_url
        }):
            response = lambda_handler(event, context)
        
        assert response["status"] == "error"
        assert "Missing bucket or key in event" in response["message"]

    @mock_aws
    def test_lambda_handler_secrets_manager_failure(self):
        """Test handling when Secrets Manager fails to retrieve secret"""
        
        # Don't create the secret to trigger failure
        event = self.create_s3_event("test-bucket", "videos/test_video.mp4")
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            with pytest.raises(Exception):
                lambda_handler(event, context)

    @mock_aws
    @patch('lambda_function.VectorDBService')
    def test_persist_task_metadata_success(self, mock_vector_db_service):
        """Test successful task metadata persistence"""
        mock_vector_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        metadata = {
            "sqs_message_id": "test-message-123",
            "s3_bucket": "test-bucket",
            "s3_key": "test-key.mp4",
            "status": "processing"
        }
        
        # Create a mock logger
        mock_logger = MagicMock()
        
        persist_task_metadata(mock_vector_db_instance, metadata, logger=mock_logger)
        
        mock_vector_db_instance.store_task.assert_called_once_with(metadata)
        mock_logger.info.assert_called_once()

    @mock_aws
    @patch('lambda_function.VectorDBService')
    def test_persist_task_metadata_failure(self, mock_vector_db_service):
        """Test task metadata persistence failure"""
        mock_vector_db_instance = MagicMock()
        mock_vector_db_instance.store_task.side_effect = Exception("Database error")
        mock_vector_db_service.return_value = mock_vector_db_instance
        
        metadata = {
            "sqs_message_id": "test-message-123",
            "s3_bucket": "test-bucket", 
            "s3_key": "test-key.mp4",
            "status": "processing"
        }
        
        mock_logger = MagicMock()
        
        persist_task_metadata(
            mock_vector_db_instance, 
            metadata, 
            fallback_status="failed",
            logger=mock_logger
        )
        
        mock_vector_db_instance.store_task.assert_called_once_with(metadata)
        mock_logger.error.assert_called()  # Should log the error