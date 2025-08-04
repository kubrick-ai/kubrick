import sys
import os
import pytest
import boto3
import json
from moto import mock_aws
from unittest.mock import patch, MagicMock

# Path to layers
layers_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../layers"))
sys.path.insert(0, os.path.join(layers_dir, "vector_database_layer"))
sys.path.insert(0, os.path.join(layers_dir, "config_layer"))

# Lambda handler path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../s3_delete_handler")))

from lambda_function import lambda_handler


class TestLambdaHandler:
    def create_s3_delete_event(self, bucket, key, event_name="ObjectRemoved:Delete"):
        """Helper to create S3 delete event for testing"""
        return {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": "us-east-1",
                    "eventTime": "2024-01-01T00:00:00.000Z",
                    "eventName": event_name,
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "test-config",
                        "bucket": {
                            "name": bucket,
                            "ownerIdentity": {"principalId": "test-principal"}
                        },
                        "object": {
                            "key": key,
                            "size": 1024,
                            "eTag": "test-etag"
                        }
                    }
                }
            ]
        }

    def create_multi_record_s3_event(self, records_data):
        """Helper to create S3 event with multiple records"""
        records = []
        for record_data in records_data:
            records.append({
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "2024-01-01T00:00:00.000Z",
                "eventName": record_data.get("event_name", "ObjectRemoved:Delete"),
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "test-config",
                    "bucket": {
                        "name": record_data["bucket"],
                        "ownerIdentity": {"principalId": "test-principal"}
                    },
                    "object": {
                        "key": record_data["key"],
                        "size": 1024,
                        "eTag": "test-etag"
                    }
                }
            })
        return {"Records": records}

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_successful_video_deletion(self, mock_is_valid_video, mock_vector_db_service):
        """Test successful deletion of video record from database"""
        mock_is_valid_video.return_value = True
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_video.return_value = [{"id": 1, "filename": "test.mp4"}]
        mock_db_instance.delete_video.return_value = True
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = {
            "DB_USERNAME": "test_user",
            "DB_PASSWORD": "test_pass"
        }
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps(secret_value)
        )

        # Create S3 delete event
        event = self.create_s3_delete_event("test-bucket", "videos/test.mp4")
        context = {}

        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            result = lambda_handler(event, context)

        mock_is_valid_video.assert_called_once_with("videos/test.mp4")
        mock_db_instance.fetch_video.assert_called_once_with(bucket="test-bucket", key="videos/test.mp4")
        mock_db_instance.delete_video.assert_called_once_with(bucket="test-bucket", key="videos/test.mp4")

        assert result is None

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_video_not_found_in_db(self, mock_is_valid_video, mock_vector_db_service):
        """Test when video file is valid but not found in database"""
        mock_is_valid_video.return_value = True
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_video.return_value = []  # No records found
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        event = self.create_s3_delete_event("test-bucket", "videos/missing.mp4")
        context = {}

        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            lambda_handler(event, context)

        # Should fetch but not attempt to delete
        mock_db_instance.fetch_video.assert_called_once_with(bucket="test-bucket", key="videos/missing.mp4")
        mock_db_instance.delete_video.assert_not_called()

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_invalid_video_file(self, mock_is_valid_video, mock_vector_db_service):
        """Test when file is not a valid video file"""
        mock_is_valid_video.return_value = False
        mock_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        event = self.create_s3_delete_event("test-bucket", "documents/readme.txt")
        context = {}

        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            lambda_handler(event, context)

        # Should check validity but not proceed with database operations
        mock_is_valid_video.assert_called_once_with("documents/readme.txt")
        mock_db_instance.fetch_video.assert_not_called()
        mock_db_instance.delete_video.assert_not_called()

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_delete_failure(self, mock_is_valid_video, mock_vector_db_service):
        """Test when video is found but deletion fails"""
        mock_is_valid_video.return_value = True
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_video.return_value = [{"id": 1, "filename": "test.mp4"}]
        mock_db_instance.delete_video.return_value = False  # Deletion failed
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        event = self.create_s3_delete_event("test-bucket", "videos/test.mp4")
        context = {}

        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            lambda_handler(event, context)

        # Should attempt deletion but handle failure gracefully
        mock_db_instance.fetch_video.assert_called_once()
        mock_db_instance.delete_video.assert_called_once()

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_multiple_records(self, mock_is_valid_video, mock_vector_db_service):
        """Test processing multiple S3 delete records in single event"""
        mock_is_valid_video.side_effect = [True, False, True]  # Mixed valid/invalid files
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_video.side_effect = [
            [{"id": 1, "filename": "video1.mp4"}],  # First video exists
            [{"id": 2, "filename": "video3.mov"}]   # Third video exists
        ]
        mock_db_instance.delete_video.side_effect = [True, True]  # Both deletions succeed
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        # Create event with multiple records
        records_data = [
            {"bucket": "test-bucket", "key": "videos/video1.mp4"},
            {"bucket": "test-bucket", "key": "documents/file.txt"},  # Invalid
            {"bucket": "test-bucket", "key": "videos/video3.mov"}
        ]
        event = self.create_multi_record_s3_event(records_data)
        context = {}

        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            lambda_handler(event, context)

        # Verify all files were checked for validity
        assert mock_is_valid_video.call_count == 3
        mock_is_valid_video.assert_any_call("videos/video1.mp4")
        mock_is_valid_video.assert_any_call("documents/file.txt")
        mock_is_valid_video.assert_any_call("videos/video3.mov")

        # Only valid video files should trigger database operations
        assert mock_db_instance.fetch_video.call_count == 2
        assert mock_db_instance.delete_video.call_count == 2

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_missing_bucket_or_key(self, mock_is_valid_video, mock_vector_db_service):
        """Test handling of malformed S3 events with missing bucket or key"""
        mock_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        # Create malformed event
        event = {
            "Records": [
                {
                    "eventName": "ObjectRemoved:Delete",
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        # Missing object key
                    }
                },
                {
                    "eventName": "ObjectRemoved:Delete",
                    "s3": {
                        # Missing bucket
                        "object": {"key": "test.mp4"}
                    }
                }
            ]
        }
        context = {}

        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            lambda_handler(event, context)

        # Should not process any records due to missing data
        mock_is_valid_video.assert_not_called()
        mock_db_instance.fetch_video.assert_not_called()
        mock_db_instance.delete_video.assert_not_called()

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_url_encoded_key(self, mock_is_valid_video, mock_vector_db_service):
        """Test handling of URL-encoded S3 keys"""
        mock_is_valid_video.return_value = True
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_video.return_value = [{"id": 1}]
        mock_db_instance.delete_video.return_value = True
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        # Create event with URL-encoded key (spaces and special chars)
        encoded_key = "videos/my%20video%20file%281%29.mp4"
        decoded_key = "videos/my video file(1).mp4"
        event = self.create_s3_delete_event("test-bucket", encoded_key)
        context = {}

        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            lambda_handler(event, context)

        # Should use decoded key for validation and database operations
        mock_is_valid_video.assert_called_once_with(decoded_key)
        mock_db_instance.fetch_video.assert_called_once_with(bucket="test-bucket", key=decoded_key)
        mock_db_instance.delete_video.assert_called_once_with(bucket="test-bucket", key=decoded_key)

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_empty_records(self, mock_is_valid_video, mock_vector_db_service):
        """Test handling of event with no records"""
        mock_db_instance = MagicMock()
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        event = {"Records": []}
        context = {}

        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            lambda_handler(event, context)

        # Should not process anything
        mock_is_valid_video.assert_not_called()
        mock_db_instance.fetch_video.assert_not_called()
        mock_db_instance.delete_video.assert_not_called()

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_database_exception(self, mock_is_valid_video, mock_vector_db_service):
        """Test handling of database exceptions"""
        mock_is_valid_video.return_value = True
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_video.side_effect = Exception("Database connection failed")
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        event = self.create_s3_delete_event("test-bucket", "videos/test.mp4")
        context = {}

        # Should not raise exception - lambda catches and logs it
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            result = lambda_handler(event, context)

        assert result is None
        mock_is_valid_video.assert_called_once()
        mock_db_instance.fetch_video.assert_called_once()

    @mock_aws
    def test_lambda_handler_secrets_error(self):
        """Test when secrets retrieval fails"""
        event = self.create_s3_delete_event("test-bucket", "videos/test.mp4")
        context = {}

        # No secret created - should raise exception
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            with pytest.raises(Exception):
                lambda_handler(event, context)

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_various_video_extensions(self, mock_is_valid_video, mock_vector_db_service):
        """Test processing different video file extensions"""
        mock_is_valid_video.side_effect = [True, True, True, True]
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_video.return_value = []
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        # Test various video extensions
        video_files = [
            "videos/test.mp4",
            "videos/test.mov",
            "videos/test.avi",
            "videos/test.mkv"
        ]

        for video_file in video_files:
            event = self.create_s3_delete_event("test-bucket", video_file)
            context = {}

            with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
                lambda_handler(event, context)

        # Should process all video files
        assert mock_is_valid_video.call_count == len(video_files)
        assert mock_db_instance.fetch_video.call_count == len(video_files)

    @mock_aws
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.is_valid_video_file')
    def test_lambda_handler_whitespace_in_key(self, mock_is_valid_video, mock_vector_db_service):
        """Test handling of S3 keys with leading/trailing whitespace"""
        mock_is_valid_video.return_value = True
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_video.return_value = []
        mock_vector_db_service.return_value = mock_db_instance

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )

        # Key with whitespace that should be stripped
        key_with_whitespace = "  videos/test.mp4  "
        trimmed_key = "videos/test.mp4"
        
        event = self.create_s3_delete_event("test-bucket", key_with_whitespace)
        context = {}

        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            lambda_handler(event, context)

        # Should use trimmed key
        mock_is_valid_video.assert_called_once_with(trimmed_key)
        mock_db_instance.fetch_video.assert_called_once_with(bucket="test-bucket", key=trimmed_key)