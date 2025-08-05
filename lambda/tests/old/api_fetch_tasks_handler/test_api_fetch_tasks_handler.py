import sys
import os
import pytest
import boto3
import json
from moto import mock_aws
from unittest.mock import patch, MagicMock

# Path to layers
layers_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../layers"))
sys.path.insert(0, os.path.join(layers_dir, "response_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "vector_database_layer"))
sys.path.insert(0, os.path.join(layers_dir, "s3_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "config_layer"))

# Lambda handler path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../api_fetch_tasks_handler")))

from lambda_function import lambda_handler


class TestLambdaHandler:
    
    @mock_aws
    @patch('lambda_function.VectorDBService')
    def test_lambda_handler_success(self, mock_vector_db_service):
        mock_vector_db = MagicMock()
        mock_vector_db.fetch_tasks.return_value = (
            [
                {
                    "id": 1,
                    "sqs_message_id": "msg-123",
                    "s3_bucket": "test-bucket",
                    "s3_key": "test-key.mp4",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00",
                    "status": "completed"
                }
            ],
            1
        )
        mock_vector_db_service.return_value = mock_vector_db
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = {
            "DB_USERNAME": "test_user",
            "DB_PASSWORD": "test_pass"
        }
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps(secret_value)
        )
        
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {
                "limit": "5",
                "page": "1"
            }
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "data" in body
        assert "metadata" in body
        assert body["metadata"]["total"] == 1
        assert body["metadata"]["limit"] == 5
        assert body["metadata"]["page"] == 1
        assert len(body["data"]) == 1
        assert body["data"][0]["status"] == "completed"
        
        mock_vector_db.fetch_tasks.assert_called_once_with(page=1, limit=5)

    @mock_aws
    @patch('lambda_function.VectorDBService')
    def test_lambda_handler_default_params(self, mock_vector_db_service):
        mock_vector_db = MagicMock()
        mock_vector_db.fetch_tasks.return_value = ([], 0)
        mock_vector_db_service.return_value = mock_vector_db

        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )
        
        event = {"httpMethod": "GET"}
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["metadata"]["limit"] == 10
        assert body["metadata"]["page"] == 0
        
        mock_vector_db.fetch_tasks.assert_called_once_with(page=0, limit=10)

    @mock_aws
    @patch('lambda_function.VectorDBService')
    def test_lambda_handler_limit_validation(self, mock_vector_db_service):
        mock_vector_db = MagicMock()
        mock_vector_db.fetch_tasks.return_value = ([], 0)
        mock_vector_db_service.return_value = mock_vector_db
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )
        
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {
                "limit": "100",  # Should be capped at 50
                "page": "-5"     # Should be set to 0
            }
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["metadata"]["limit"] == 50  # Capped at MAX_TASK_LIMIT
        assert body["metadata"]["page"] == 0    # Min value is 0
        
        mock_vector_db.fetch_tasks.assert_called_once_with(page=0, limit=50)

    @mock_aws  
    def test_lambda_handler_invalid_params(self):
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )
        
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {
                "limit": "invalid",
                "page": "also_invalid"
            }
        }
        context = {}
        
        with patch('lambda_function.VectorDBService') as mock_vector_db_service, \
             patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            
            mock_vector_db = MagicMock()
            mock_vector_db_service.return_value = mock_vector_db
            
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "error" in body
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "Invalid 'limit' or 'page' parameter" in body["error"]["message"]
        
        mock_vector_db_service.assert_called_once()
        mock_vector_db.fetch_tasks.assert_not_called()

    @mock_aws
    @patch('lambda_function.VectorDBService')
    def test_lambda_handler_database_error(self, mock_vector_db_service):
        mock_vector_db = MagicMock()
        mock_vector_db.fetch_tasks.side_effect = Exception("Database connection failed")
        mock_vector_db_service.return_value = mock_vector_db
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )
        
        event = {"httpMethod": "GET"}
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body
        assert body["error"]["message"] == "Internal server error"

    def test_lambda_handler_secrets_error(self):
        """Test when secrets retrieval fails - current lambda function doesn't handle this"""
        with patch('lambda_function.get_secret') as mock_get_secret:
            mock_get_secret.side_effect = Exception("Failed to retrieve secret")
            
            event = {"httpMethod": "GET"}
            context = {}
            
            # Current lambda function doesn't have try/catch, so exception propagates
            with pytest.raises(Exception, match="Failed to retrieve secret"):
                lambda_handler(event, context)

    @mock_aws
    def test_lambda_handler_with_environment_variables(self):
        # Use a fresh AWS session to avoid secret conflicts
        import uuid
        test_secret_name = f"test_secret_{uuid.uuid4().hex[:8]}"
        
        # Setup Secrets Manager with unique name
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name=test_secret_name,
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )
        
        # Mock the module-level constants since they're set at import time
        with patch('lambda_function.VectorDBService') as mock_vector_db_service, \
             patch('lambda_function.SECRET_NAME', test_secret_name), \
             patch('lambda_function.DEFAULT_TASK_LIMIT', 20), \
             patch('lambda_function.MAX_TASK_LIMIT', 100), \
             patch('lambda_function.DEFAULT_TASK_PAGE', 2), \
             patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            
            mock_vector_db = MagicMock()
            mock_vector_db.fetch_tasks.return_value = ([], 0)
            mock_vector_db_service.return_value = mock_vector_db
            
            event = {"httpMethod": "GET"}
            context = {}
            
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert body["metadata"]["limit"] == 20  # Custom DEFAULT_TASK_LIMIT
        assert body["metadata"]["page"] == 2    # Custom DEFAULT_TASK_PAGE
        
        # Verify custom defaults were used in database call
        mock_vector_db.fetch_tasks.assert_called_once_with(page=2, limit=20)

    @mock_aws
    @patch('lambda_function.VectorDBService')
    def test_lambda_handler_boundary_conditions(self, mock_vector_db_service):
        # Test with limit=0 (should become 1) and very high limit
        mock_vector_db = MagicMock()
        mock_vector_db.fetch_tasks.return_value = ([], 0)
        mock_vector_db_service.return_value = mock_vector_db
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"DB_USERNAME": "test", "DB_PASSWORD": "test"})
        )
        
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {
                "limit": "0",  # Should become 1 (minimum)
                "page": "0"
            }
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["metadata"]["limit"] == 1  # Minimum enforced
        
        # Verify minimum limit was used
        mock_vector_db.fetch_tasks.assert_called_once_with(page=0, limit=1)