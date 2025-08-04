import sys
import os
import pytest
import boto3
import json
import base64
from moto import mock_aws
from unittest.mock import patch, MagicMock

# Path to layers
layers_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../layers"))
sys.path.insert(0, os.path.join(layers_dir, "embed_service_layer"))
sys.path.insert(0, os.path.join(layers_dir, "response_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "vector_database_layer"))
sys.path.insert(0, os.path.join(layers_dir, "s3_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "config_layer"))

# Lambda handler path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../api_search_handler")))

from lambda_function import lambda_handler

class TestLambdaHandler:
    
    def create_multipart_form_data(self, fields):
        """Helper to create multipart/form-data for testing"""
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_parts = []
        
        for field_name, field_value in fields.items():
            if isinstance(field_value, dict) and 'content' in field_value:
                # File field
                content = field_value['content']
                filename = field_value.get('filename', 'test_file')
                content_type = field_value.get('content_type', 'application/octet-stream')
                
                # Add headers as bytes
                header = (f'--{boundary}\r\n'
                        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                        f'Content-Type: {content_type}\r\n\r\n').encode('utf-8')
                body_parts.append(header)
                
                # Add content (handle both string and bytes)
                if isinstance(content, str):
                    body_parts.append(content.encode('utf-8'))
                else:
                    body_parts.append(content)  # Already bytes
                
                body_parts.append(b'\r\n')
            else:
                # Text field
                field_data = (f'--{boundary}\r\n'
                            f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n').encode('utf-8')
                body_parts.append(field_data)
                
                if isinstance(field_value, (dict, list)):
                    body_parts.append(json.dumps(field_value).encode('utf-8'))
                else:
                    body_parts.append(str(field_value).encode('utf-8'))
                
                body_parts.append(b'\r\n')
        
        # Add final boundary
        body_parts.append(f'--{boundary}--\r\n'.encode('utf-8'))
        
        # Join all parts as bytes
        body = b''.join(body_parts)
        
        return body, boundary

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_text_search_success(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.return_value = (
            [
                {
                    "id": 1,
                    "similarity": 0.85,
                    "video": {
                        "id": 1,
                        "filename": "test_video.mp4",
                        "s3_bucket": "test-bucket",
                        "s3_key": "test-key.mp4"
                    }
                }
            ],
            {"page": 0, "limit": 10, "total": 1}
        )
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = {
            "DB_USERNAME": "test_user",
            "DB_PASSWORD": "test_pass",
            "TWELVELABS_API_KEY": "test_api_key_12345"
        }
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps(secret_value)
        )
        
        # Create multipart form data
        form_fields = {
            "query_type": "text",
            "query_text": "test search query",
            "page_limit": "10"
        }
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            },
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body_data = json.loads(response["body"])
        assert "data" in body_data
        assert "metadata" in body_data
        assert len(body_data["data"]) == 1
        assert body_data["data"][0]["similarity"] == 0.85
        
        mock_embed_service.assert_called_once()
        mock_vector_db_service.assert_called_once()
        mock_search_controller.assert_called_once()
        mock_search_controller_instance.process_search_request.assert_called_once_with(event)

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_image_search_success(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.return_value = (
            [
                {
                    "id": 2,
                    "similarity": 0.92,
                    "video": {
                        "id": 2,
                        "filename": "test_image_match.mp4",
                        "s3_bucket": "test-bucket",
                        "s3_key": "image-match.mp4"
                    }
                }
            ],
            {"page": 0, "limit": 5, "total": 1}
        )
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({
                "DB_USERNAME": "test",
                "DB_PASSWORD": "test",
                "TWELVELABS_API_KEY": "test_key"
            })
        )
        
        # Create multipart form data with image file
        form_fields = {
            "query_type": "image",
            "page_limit": "5",
            "query_media_file": {
                "content": b"fake_image_data",
                "filename": "test.jpg",
                "content_type": "image/jpeg"
            }
        }
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {
                "Content-Type": f"multipart/form-data; boundary={boundary}"
            },
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body_data = json.loads(response["body"])
        assert len(body_data["data"]) == 1
        assert body_data["metadata"]["limit"] == 5

    @mock_aws
    def test_lambda_handler_options_request(self):
        """Test CORS preflight OPTIONS request"""
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        event = {"httpMethod": "OPTIONS"}
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "POST" in response["headers"]["Access-Control-Allow-Methods"]
        assert "OPTIONS" in response["headers"]["Access-Control-Allow-Methods"]
        assert response["body"] == ""

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_search_request_error(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        from search_errors import SearchRequestError
        
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.side_effect = SearchRequestError("Invalid query parameters")
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {"query_type": "text"}
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "INVALID_REQUEST"
        assert "Invalid query parameters" in body_data["error"]["message"]

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_embedding_error(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        from search_errors import EmbeddingError
        
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.side_effect = EmbeddingError("Failed to extract text embedding")
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {"query_type": "text", "query_text": "test"}
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 422
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "EMBEDDING_ERROR"

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_media_processing_error(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        from search_errors import MediaProcessingError
        
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.side_effect = MediaProcessingError("Invalid media file format")
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {"query_type": "image", "query_media_url": "http://example.com/image.jpg"}
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 422
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "MEDIA_PROCESSING_ERROR"

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_database_error(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        from search_errors import DatabaseError
        
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.side_effect = DatabaseError("Vector database connection failed")
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {"query_type": "text", "query_text": "test"}
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 503
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "DATABASE_ERROR"
        assert body_data["error"]["message"] == "Search service temporarily unavailable"

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_general_search_error(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        from search_errors import SearchError
        
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.side_effect = SearchError("General search failure")
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {"query_type": "text", "query_text": "test"}
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 500
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "INTERNAL_ERROR"

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_pydantic_validation_error(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        from pydantic import ValidationError
        
        mock_search_controller_instance = MagicMock()
        # Create a realistic ValidationError
        try:
            from pydantic import BaseModel, Field
            class TestModel(BaseModel):
                required_field: str = Field(..., min_length=1)
            TestModel(required_field="")  # This will raise ValidationError
        except ValidationError as e:
            mock_search_controller_instance.process_search_request.side_effect = e
        
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {"query_type": "text"}
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "VALIDATION_ERROR"
        assert "Invalid request format" in body_data["error"]["message"]

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_unexpected_error(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.side_effect = RuntimeError("Unexpected system error")
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {"query_type": "text", "query_text": "test"}
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 500
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "INTERNAL_ERROR"
        assert body_data["error"]["message"] == "Internal server error"

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_environment_variables(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        """Test that environment variables are properly used in service initialization"""
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.return_value = ([], {"page": 0, "limit": 10, "total": 0})
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="test_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "custom_api_key"})
        )
        
        form_fields = {"query_type": "text", "query_text": "test"}
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        env_vars = {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'EMBEDDING_MODEL_NAME': 'Custom-Model-Name',
            'DEFAULT_CLIP_LENGTH': '12',
            'QUERY_MEDIA_FILE_SIZE_LIMIT': '8000000'
        }
        
        # Mock the module-level constants since they're evaluated at import time
        with patch.dict('os.environ', env_vars), \
             patch('lambda_function.SECRET_NAME', 'test_secret'), \
             patch('lambda_function.EMBEDDING_MODEL_NAME', 'Custom-Model-Name'), \
             patch('lambda_function.DEFAULT_CLIP_LENGTH', 12), \
             patch('lambda_function.QUERY_MEDIA_FILE_SIZE_LIMIT', 8000000):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        
        # Verify EmbedService was initialized with custom values
        mock_embed_service.assert_called_once_with(
            api_key="custom_api_key",
            model_name="Custom-Model-Name",
            clip_length=12,
            logger=mock_embed_service.call_args[1]['logger']
        )
        
        # Verify SearchController was initialized with custom file size limit
        args, kwargs = mock_search_controller.call_args
        assert kwargs['query_media_file_size_limit'] == 8000000

    @mock_aws
    def test_lambda_handler_secrets_error(self):
        """Test when secrets retrieval fails"""
        
        form_fields = {"query_type": "text", "query_text": "test"}
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            with pytest.raises(Exception):
                lambda_handler(event, context)

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_plaintext_body_error(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        """Test that plain text body causes issues as expected"""
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.side_effect = Exception("Failed to parse plaintext as multipart")
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        # Send plain text instead of multipart form-data
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"query_type": "text", "query_text": "test"}),
            "isBase64Encoded": False
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 500
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "INTERNAL_ERROR"

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_video_search_with_modality(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        """Test video search with query_modality parameter"""
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.return_value = (
            [
                {
                    "id": 3,
                    "similarity": 0.78,
                    "modality": "visual-text",
                    "video": {
                        "id": 3,
                        "filename": "test_video.mp4",
                        "s3_bucket": "test-bucket",
                        "s3_key": "video-match.mp4"
                    }
                }
            ],
            {"page": 0, "limit": 10, "total": 1}
        )
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {
            "query_type": "video",
            "query_media_url": "https://example.com/test_video.mp4",
            "query_modality": ["visual-text", "audio"],
            "page_limit": "10",
            "min_similarity": "0.3"
        }
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body_data = json.loads(response["body"])
        assert len(body_data["data"]) == 1
        assert body_data["data"][0]["modality"] == "visual-text"

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_audio_search_with_url(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        """Test audio search using URL instead of file upload"""
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.return_value = (
            [
                {
                    "id": 4,
                    "similarity": 0.65,
                    "video": {
                        "id": 4,
                        "filename": "audio_match.mp4",
                        "s3_bucket": "test-bucket",
                        "s3_key": "audio-content.mp4"
                    }
                }
            ],
            {"page": 0, "limit": 15, "total": 1}
        )
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {
            "query_type": "audio",
            "query_media_url": "https://example.com/test_audio.mp3",
            "page_limit": "15"
        }
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body_data = json.loads(response["body"])
        assert len(body_data["data"]) == 1
        assert body_data["metadata"]["limit"] == 15
        assert body_data["data"][0]["similarity"] == 0.65

    @mock_aws
    @patch('lambda_function.SearchController')
    @patch('lambda_function.VectorDBService')
    @patch('lambda_function.EmbedService')
    def test_lambda_handler_search_with_filter(self, mock_embed_service, mock_vector_db_service, mock_search_controller):
        """Test search with filter parameters"""
        mock_search_controller_instance = MagicMock()
        mock_search_controller_instance.process_search_request.return_value = (
            [
                {
                    "id": 5,
                    "similarity": 0.88,
                    "scope": "clip",
                    "modality": "visual-text",
                    "video": {
                        "id": 5,
                        "filename": "filtered_result.mp4",
                        "s3_bucket": "test-bucket",
                        "s3_key": "filtered.mp4"
                    }
                }
            ],
            {"page": 0, "limit": 10, "total": 1}
        )
        mock_search_controller.return_value = mock_search_controller_instance
        
        secretsmanager = boto3.client("secretsmanager", region_name="us-east-1")
        secretsmanager.create_secret(
            Name="kubrick_secret",
            SecretString=json.dumps({"TWELVELABS_API_KEY": "test"})
        )
        
        form_fields = {
            "query_type": "text",
            "query_text": "test with filter",
            "filter": {"scope": "clip", "modality": "visual-text"},
            "min_similarity": "0.5"
        }
        body, boundary = self.create_multipart_form_data(form_fields)
        
        event = {
            "httpMethod": "POST",
            "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
            "body": base64.b64encode(body).decode('utf-8'),
            "isBase64Encoded": True
        }
        context = {}
        
        with patch.dict('os.environ', {'AWS_DEFAULT_REGION': 'us-east-1'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body_data = json.loads(response["body"])
        assert len(body_data["data"]) == 1
        assert body_data["data"][0]["scope"] == "clip"
        assert body_data["data"][0]["modality"] == "visual-text"