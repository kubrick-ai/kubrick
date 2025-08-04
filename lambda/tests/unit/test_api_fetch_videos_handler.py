import sys
import os
import boto3
import json
from moto import mock_aws
from unittest.mock import patch, MagicMock

# Path to layers
layers_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/layers")
)
sys.path.insert(0, os.path.join(layers_dir, "response_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "vector_database_layer"))
sys.path.insert(0, os.path.join(layers_dir, "s3_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "config_layer"))

# Insert lambda src into path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/")),
)

from api_fetch_videos_handler.lambda_function import lambda_handler  # noqa: E402


class TestLambdaHandler:
    @mock_aws
    @patch("api_fetch_videos_handler.lambda_function.VectorDBService")
    @patch("api_fetch_videos_handler.lambda_function.add_presigned_urls")
    def test_lambda_handler_success(
        self, mock_add_presigned_urls, mock_vector_db_service
    ):
        # Setup mocks
        mock_vector_db = MagicMock()
        mock_vector_db.fetch_videos.return_value = (
            [
                {
                    "id": 1,
                    "filename": "test.mp4",
                    "s3_bucket": "test-bucket",
                    "s3_key": "test-key",
                    "duration": 120.5,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00",
                    "height": 720,
                    "width": 1280,
                }
            ],
            1,
        )
        mock_vector_db_service.return_value = mock_vector_db

        # Setup Secrets Manager
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = {"DB_USERNAME": "test_user", "DB_PASSWORD": "test_pass"}
        secretsmanager.create_secret(
            Name="kubrick_secret", SecretString=json.dumps(secret_value)
        )

        # Test event
        event = {"queryStringParameters": {"limit": "10", "page": "0"}}
        context = {}

        # Execute with proper region
        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
            response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "data" in body
        assert "metadata" in body
        assert body["metadata"]["total"] == 1
        assert body["metadata"]["limit"] == 10
        assert body["metadata"]["page"] == 0
        assert len(body["data"]) == 1

        mock_vector_db.fetch_videos.assert_called_once_with(page=0, limit=10)
        mock_add_presigned_urls.assert_called_once()

    @mock_aws
    @patch("api_fetch_videos_handler.lambda_function.VectorDBService")
    def test_lambda_handler_default_params(self, mock_vector_db_service):
        mock_vector_db = MagicMock()
        mock_vector_db.fetch_videos.return_value = ([], 0)
        mock_vector_db_service.return_value = mock_vector_db

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"}),
        )

        event = {}
        context = {}

        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
            response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["metadata"]["limit"] == 12
        assert body["metadata"]["page"] == 0

        mock_vector_db.fetch_videos.assert_called_once_with(page=0, limit=12)

    @mock_aws
    @patch("api_fetch_videos_handler.lambda_function.VectorDBService")
    def test_lambda_handler_database_error(self, mock_vector_db_service):
        mock_vector_db = MagicMock()
        mock_vector_db.fetch_videos.side_effect = Exception(
            "Database connection failed"
        )
        mock_vector_db_service.return_value = mock_vector_db

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"}),
        )

        event = {}
        context = {}

        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
            response = lambda_handler(event, context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body
        assert body["error"]["message"] == "Internal server error"

    @patch("api_fetch_videos_handler.lambda_function.get_secret")
    def test_lambda_handler_secrets_error(self, mock_get_secret):
        mock_get_secret.side_effect = Exception("Failed to retrieve secret")

        event = {}
        context = {}

        response = lambda_handler(event, context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body
        assert body["error"]["message"] == "Internal server error"

    @mock_aws
    @patch("api_fetch_videos_handler.lambda_function.VectorDBService")
    def test_lambda_handler_invalid_params(self, mock_vector_db_service):
        mock_vector_db = MagicMock()
        mock_vector_db.fetch_videos.return_value = ([], 0)
        mock_vector_db_service.return_value = mock_vector_db

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"}),
        )

        event = {"queryStringParameters": {"limit": "invalid", "page": "also_invalid"}}
        context = {}

        with patch.dict("os.environ", {"AWS_DEFAULT_REGION": "us-east-1"}):
            response = lambda_handler(event, context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body

    @mock_aws
    @patch("api_fetch_videos_handler.lambda_function.add_presigned_urls")
    @patch("api_fetch_videos_handler.lambda_function.get_secret")
    def test_lambda_handler_with_environment_variables(
        self, mock_get_secret, mock_add_presigned_urls
    ):
        # Mock the SECRET_NAME at module level
        with patch(
            "api_fetch_videos_handler.lambda_function.SECRET_NAME", "custom_secret"
        ), patch(
            "api_fetch_videos_handler.lambda_function.PRESIGNED_URL_EXPIRY", 7200
        ), patch(
            "api_fetch_videos_handler.lambda_function.VectorDBService"
        ) as mock_vector_db_service:

            mock_vector_db = MagicMock()
            mock_vector_db.fetch_videos.return_value = ([], 0)
            mock_vector_db_service.return_value = mock_vector_db
            mock_get_secret.return_value = {
                "DB_USERNAME": "test",
                "DB_PASSWORD": "test",
            }

            event = {}
            context = {}

            response = lambda_handler(event, context)

        assert response["statusCode"] == 200

        mock_get_secret.assert_called_once_with("custom_secret")
        mock_add_presigned_urls.assert_called_once_with([], 7200)
