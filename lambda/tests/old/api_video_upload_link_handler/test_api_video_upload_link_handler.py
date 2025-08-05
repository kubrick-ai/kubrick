import sys
import os
import pytest
import json
from moto import mock_aws
from unittest.mock import patch, MagicMock

# Path to layers
layers_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../layers"))
sys.path.insert(0, os.path.join(layers_dir, "response_utils_layer"))
sys.path.insert(0, os.path.join(layers_dir, "s3_utils_layer"))

# Lambda handler path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../api_video_upload_link_handler")))

from lambda_function import lambda_handler


class TestLambdaHandler:
    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    def test_lambda_handler_valid_mp4_file_success(self, mock_generate_presigned_url):
        """Test successful presigned URL generation for valid MP4 file"""
        mock_presigned_url = "https://jorge-video-upload-bucket.s3.us-east-1.amazonaws.com/uploads/12345/test_video.mp4?AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE&Expires=1234567890&Signature=example"
        mock_generate_presigned_url.return_value = mock_presigned_url
        
        event = {
            "queryStringParameters": {
                "filename": "test_video.mp4"
            }
        }
        context = {}
        
        with patch.dict('os.environ', {
            'S3_BUCKET_NAME': 'jorge-video-upload-bucket',
            'PRESIGNED_URL_EXPIRATION': '3600'
        }):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body_data = json.loads(response["body"])
        assert "data" in body_data
        assert body_data["data"]["presigned_url"] == mock_presigned_url
        assert body_data["data"]["filename"] == "test_video.mp4"
        assert body_data["data"]["file_extension"] == ".mp4"
        assert body_data["data"]["expires_in_seconds"] == 3600
        assert body_data["data"]["upload_method"] == "PUT"
        assert body_data["data"]["content_type"] == "video/mp4"
        
        # Verify the mock was called with correct parameters
        mock_generate_presigned_url.assert_called_once()
        call_args = mock_generate_presigned_url.call_args
        assert call_args[1]["bucket"] == "jorge-video-upload-bucket"
        assert call_args[1]["client_method"] == "put_object"
        assert call_args[1]["content_type"] == "video/mp4"
        assert call_args[1]["expires_in"] == 600  # PRESIGNED_URL_TTL
        assert "uploads/" in call_args[1]["key"]
        assert call_args[1]["key"].endswith("/test_video.mp4")

    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    def test_lambda_handler_various_file_extensions(self, mock_generate_presigned_url):
        """Test presigned URL generation for various supported file extensions"""
        
        test_cases = [
            ("video.mov", ".mov", "video/quicktime", "https://test-video-bucket.s3.us-east-1.amazonaws.com/uploads/uuid1/video.mov?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
            ("presentation.avi", ".avi", "video/x-msvideo", "https://test-video-bucket.s3.us-east-1.amazonaws.com/uploads/uuid2/presentation.avi?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
            ("movie.mkv", ".mkv", "video/x-matroska", "https://test-video-bucket.s3.us-east-1.amazonaws.com/uploads/uuid3/movie.mkv?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
            ("clip.webm", ".webm", "video/webm", "https://test-video-bucket.s3.us-east-1.amazonaws.com/uploads/uuid4/clip.webm?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
            ("old_video.wmv", ".wmv", "video/x-ms-wmv", "https://test-video-bucket.s3.us-east-1.amazonaws.com/uploads/uuid5/old_video.wmv?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
            ("broadcast.ts", ".ts", "video/mp2t", "https://test-video-bucket.s3.us-east-1.amazonaws.com/uploads/uuid6/broadcast.ts?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
        ]
        
        for filename, expected_ext, expected_content_type, mock_url in test_cases:
            mock_generate_presigned_url.reset_mock()
            mock_generate_presigned_url.return_value = mock_url
            
            event = {
                "queryStringParameters": {
                    "filename": filename
                }
            }
            
            with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-video-bucket'}):
                response = lambda_handler(event, {})
            
            assert response["statusCode"] == 200
            body_data = json.loads(response["body"])
            assert body_data["data"]["filename"] == filename
            assert body_data["data"]["file_extension"] == expected_ext
            assert body_data["data"]["content_type"] == expected_content_type
            assert body_data["data"]["presigned_url"] == mock_url
            
            # Verify content type was passed correctly to generate_presigned_url
            call_args = mock_generate_presigned_url.call_args
            assert call_args[1]["content_type"] == expected_content_type
            assert call_args[1]["bucket"] == "test-video-bucket"

    @mock_aws
    def test_lambda_handler_missing_query_parameters(self):
        """Test error response when queryStringParameters is missing"""
        event = {}  # No queryStringParameters
        context = {}
        
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'production-video-bucket'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "INVALID_REQUEST"
        assert "Missing query parameters" in body_data["error"]["message"]

    @mock_aws
    def test_lambda_handler_null_query_parameters(self):
        """Test error response when queryStringParameters is None"""
        event = {
            "queryStringParameters": None
        }
        context = {}
        
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'production-video-bucket'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "INVALID_REQUEST"
        assert "Missing query parameters" in body_data["error"]["message"]

    @mock_aws
    def test_lambda_handler_missing_filename_parameter(self):
        """Test error response when filename parameter is missing"""
        event = {
            "queryStringParameters": {
                "other_param": "value"
            }
        }
        context = {}
        
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'production-video-bucket'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "INVALID_REQUEST"
        assert "Missing required parameter: filename" in body_data["error"]["message"]

    @mock_aws
    def test_lambda_handler_empty_filename_parameter(self):
        """Test error response when filename parameter is empty"""
        event = {
            "queryStringParameters": {
                "filename": ""
            }
        }
        context = {}
        
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'production-video-bucket'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "INVALID_REQUEST"
        assert "Missing required parameter: filename" in body_data["error"]["message"]

    @mock_aws
    def test_lambda_handler_invalid_file_extensions(self):
        """Test error response for invalid file extensions"""
        invalid_extensions = [
            "document.pdf",
            "image.jpg", 
            "audio.mp3",
            "text.txt",
            "archive.zip",
            "video.xyz",  # Non-existent extension
            "no_extension",
            "video.",  # Empty extension
        ]
        
        for filename in invalid_extensions:
            event = {
                "queryStringParameters": {
                    "filename": filename
                }
            }
            
            with patch.dict('os.environ', {'S3_BUCKET_NAME': 'production-video-bucket'}):
                response = lambda_handler(event, {})
            
            assert response["statusCode"] == 400
            body_data = json.loads(response["body"])
            assert "Invalid video file extension" in body_data["error"]["message"]
            assert "Valid extensions:" in body_data["error"]["message"]
            # Verify some valid extensions are listed in the error message
            assert ".mp4" in body_data["error"]["message"]
            assert ".mov" in body_data["error"]["message"]

    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    def test_lambda_handler_case_insensitive_extensions(self, mock_generate_presigned_url):
        """Test that file extensions are handled case-insensitively"""
        
        test_cases = [
            ("VIDEO.MP4", ".mp4", "video/mp4", "https://media-upload-bucket.s3.us-west-2.amazonaws.com/uploads/uuid1/VIDEO.MP4?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
            ("video.Mp4", ".mp4", "video/mp4", "https://media-upload-bucket.s3.us-west-2.amazonaws.com/uploads/uuid2/video.Mp4?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
            ("VIDEO.MOV", ".mov", "video/quicktime", "https://media-upload-bucket.s3.us-west-2.amazonaws.com/uploads/uuid3/VIDEO.MOV?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
            ("file.AVI", ".avi", "video/x-msvideo", "https://media-upload-bucket.s3.us-west-2.amazonaws.com/uploads/uuid4/file.AVI?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"),
        ]
        
        for filename, expected_ext, expected_content_type, mock_url in test_cases:
            mock_generate_presigned_url.reset_mock()
            mock_generate_presigned_url.return_value = mock_url
            
            event = {
                "queryStringParameters": {
                    "filename": filename
                }
            }
            
            with patch.dict('os.environ', {'S3_BUCKET_NAME': 'media-upload-bucket'}):
                response = lambda_handler(event, {})
            
            assert response["statusCode"] == 200
            body_data = json.loads(response["body"])
            assert body_data["data"]["file_extension"] == expected_ext
            assert body_data["data"]["content_type"] == expected_content_type
            assert body_data["data"]["presigned_url"] == mock_url

    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    @patch('lambda_function.logger')
    def test_lambda_handler_s3_generate_presigned_url_error(self, mock_logger, mock_generate_presigned_url):
        """Test error handling when S3 presigned URL generation fails"""
        mock_generate_presigned_url.side_effect = Exception("S3 service unavailable")
        
        event = {
            "queryStringParameters": {
                "filename": "test_video.mp4"
            }
        }
        context = {}
        
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'production-video-bucket'}):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 500
        body_data = json.loads(response["body"])
        assert body_data["error"]["code"] == "INTERNAL_ERROR"
        assert "Internal server error" in body_data["error"]["message"]
        assert "unexpected error occurred" in body_data["error"]["message"]

    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    def test_lambda_handler_environment_variables(self, mock_generate_presigned_url):
        """Test that environment variables are properly used"""
        mock_presigned_url = "https://custom-upload-bucket.s3.us-west-1.amazonaws.com/uploads/test-uuid-456/test_video.mp4?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"
        mock_generate_presigned_url.return_value = mock_presigned_url
        
        event = {
            "queryStringParameters": {
                "filename": "test_video.mp4"
            }
        }
        context = {}
        
        custom_env = {
            'S3_BUCKET_NAME': 'custom-upload-bucket',
            'PRESIGNED_URL_EXPIRATION': '7200'  # 2 hours
        }
        
        with patch.dict('os.environ', custom_env):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body_data = json.loads(response["body"])
        
        # Check that custom expiration is used in response
        assert body_data["data"]["expires_in_seconds"] == 7200
        assert body_data["data"]["presigned_url"] == mock_presigned_url
        
        # Verify the correct bucket was passed to generate_presigned_url
        call_args = mock_generate_presigned_url.call_args
        assert call_args[1]["bucket"] == "custom-upload-bucket"
        # Note: TTL should still be 600 (PRESIGNED_URL_TTL default) despite PRESIGNED_URL_EXPIRATION being 7200
        assert call_args[1]["expires_in"] == 600

    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    def test_lambda_handler_default_environment_values(self, mock_generate_presigned_url):
        """Test behavior with default environment variable values"""
        mock_presigned_url = "https://default-video-bucket.s3.us-east-1.amazonaws.com/uploads/default-uuid/test_video.mp4?AWSAccessKeyId=EXAMPLE&Expires=1234567890&Signature=example"
        mock_generate_presigned_url.return_value = mock_presigned_url
        
        event = {
            "queryStringParameters": {
                "filename": "test_video.mp4"
            }
        }
        context = {}
        
        # Only set required S3_BUCKET_NAME, let PRESIGNED_URL_EXPIRATION use default
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'default-video-bucket'}, clear=True):
            response = lambda_handler(event, context)
        
        assert response["statusCode"] == 200
        body_data = json.loads(response["body"])
        
        # Should use default PRESIGNED_URL_EXPIRATION of 3600
        assert body_data["data"]["expires_in_seconds"] == 3600
        assert body_data["data"]["presigned_url"] == mock_presigned_url
        
        # Should use default PRESIGNED_URL_TTL of 600
        call_args = mock_generate_presigned_url.call_args
        assert call_args[1]["expires_in"] == 600
        assert call_args[1]["bucket"] == "default-video-bucket"

    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    def test_lambda_handler_uuid_in_key_generation(self, mock_generate_presigned_url):
        """Test that UUID is properly generated in S3 key"""
        mock_generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/mock-url"
        
        event = {
            "queryStringParameters": {
                "filename": "test_video.mp4"
            }
        }
        
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
            # Make multiple calls to ensure UUIDs are different
            response1 = lambda_handler(event, {})
            response2 = lambda_handler(event, {})
        
        # Both should succeed
        assert response1["statusCode"] == 200
        assert response2["statusCode"] == 200
        
        # Verify that generate_presigned_url was called with different keys (due to different UUIDs)
        assert mock_generate_presigned_url.call_count == 2
        call1_key = mock_generate_presigned_url.call_args_list[0][1]["key"]
        call2_key = mock_generate_presigned_url.call_args_list[1][1]["key"]
        
        # Both keys should follow uploads/{uuid}/{filename} pattern
        assert call1_key.startswith("uploads/")
        assert call1_key.endswith("/test_video.mp4")
        assert call2_key.startswith("uploads/")
        assert call2_key.endswith("/test_video.mp4")
        # Keys should be different due to different UUIDs
        assert call1_key != call2_key

    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    def test_lambda_handler_filename_with_spaces_and_special_chars(self, mock_generate_presigned_url):
        """Test handling of filenames with spaces and special characters"""
        mock_generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/mock-url"
        
        test_filenames = [
            "my video file.mp4",
            "video-with-dashes.mov",
            "video_with_underscores.avi",
            "video (1).mp4",
            "video[2023].mkv",
        ]
        
        for filename in test_filenames:
            mock_generate_presigned_url.reset_mock()
            
            event = {
                "queryStringParameters": {
                    "filename": filename
                }
            }
            
            with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
                response = lambda_handler(event, {})
            
            assert response["statusCode"] == 200
            body_data = json.loads(response["body"])
            assert body_data["data"]["filename"] == filename
            
            # Verify filename is preserved in the S3 key
            call_args = mock_generate_presigned_url.call_args
            assert call_args[1]["key"].endswith(f"/{filename}")

    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    def test_lambda_handler_cors_headers(self, mock_generate_presigned_url):
        """Test that proper CORS headers are included in response"""
        mock_generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/mock-url"
        
        event = {
            "queryStringParameters": {
                "filename": "test_video.mp4"
            }
        }
        
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
            response = lambda_handler(event, {})
        
        assert response["statusCode"] == 200
        assert "headers" in response
        assert response["headers"]["Content-Type"] == "application/json"
        assert "Access-Control-Allow-Origin" in response["headers"]
        
        # Test error response also has CORS headers
        event_invalid = {
            "queryStringParameters": {
                "filename": "invalid.txt"
            }
        }
        
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
            error_response = lambda_handler(event_invalid, {})
        
        assert error_response["statusCode"] == 400
        assert "headers" in error_response
        assert error_response["headers"]["Content-Type"] == "application/json"
        assert "Access-Control-Allow-Origin" in error_response["headers"]

    @mock_aws
    @patch('lambda_function.s3_utils.generate_presigned_url')
    def test_lambda_handler_response_structure(self, mock_generate_presigned_url):
        """Test the complete structure of successful response"""
        mock_presigned_url = "https://test-bucket.s3.amazonaws.com/uploads/uuid/test.mp4?signature=xyz"
        mock_generate_presigned_url.return_value = mock_presigned_url
        
        event = {
            "queryStringParameters": {
                "filename": "test.mp4"
            }
        }
        
        with patch.dict('os.environ', {
            'S3_BUCKET_NAME': 'test-bucket',
            'PRESIGNED_URL_EXPIRATION': '1800'
        }):
            response = lambda_handler(event, {})
        
        assert response["statusCode"] == 200
        assert "headers" in response
        assert "body" in response
        
        body_data = json.loads(response["body"])
        assert "data" in body_data
        assert "metadata" in body_data
        
        data = body_data["data"]
        required_fields = [
            "presigned_url", "filename", "file_extension", 
            "expires_in_seconds", "upload_method", "content_type"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        assert data["presigned_url"] == mock_presigned_url
        assert data["filename"] == "test.mp4"
        assert data["file_extension"] == ".mp4"
        assert data["expires_in_seconds"] == 1800
        assert data["upload_method"] == "PUT"
        assert data["content_type"] == "video/mp4"