import json
import pytest
from unittest.mock import patch, MagicMock


from api_video_upload_link_handler.lambda_function import lambda_handler


@pytest.fixture
def mock_generate_presigned_url():
    """Mocks the generate_presigned_url utility and yields the mock."""
    with patch(
        "api_video_upload_link_handler.lambda_function.s3_utils.generate_presigned_url"
    ) as mock_func:
        mock_func.return_value = "https://test-bucket.s3.amazonaws.com/mock-url"
        yield mock_func


def test_lambda_handler_success(
    mock_generate_presigned_url, event_builder, test_s3_bucket
):
    """Test successful presigned URL generation for a valid MP4 file."""
    event = event_builder.api_gateway_proxy_event(
        query_params={"filename": "test_video.mp4"}
    )

    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body_data = json.loads(response["body"])
    assert "data" in body_data
    assert body_data["data"]["presigned_url"]
    assert body_data["data"]["filename"] == "test_video.mp4"
    assert body_data["data"]["content_type"] == "video/mp4"

    mock_generate_presigned_url.assert_called_once()
    call_args = mock_generate_presigned_url.call_args[1]
    assert call_args["bucket"] == test_s3_bucket
    assert call_args["client_method"] == "put_object"
    assert call_args["content_type"] == "video/mp4"
    assert "uploads/" in call_args["key"]
    assert call_args["key"].endswith("/test_video.mp4")


@pytest.mark.parametrize(
    "filename, expected_ext, expected_content_type",
    [
        ("video.mov", ".mov", "video/quicktime"),
        ("presentation.avi", ".avi", "video/x-msvideo"),
        ("movie.mkv", ".mkv", "video/x-matroska"),
        ("clip.webm", ".webm", "video/webm"),
        ("old_video.wmv", ".wmv", "video/x-ms-wmv"),
        ("broadcast.ts", ".ts", "video/mp2t"),
        ("VIDEO.MP4", ".mp4", "video/mp4"),
        ("file.AVI", ".avi", "video/x-msvideo"),
    ],
)
def test_lambda_handler_various_file_extensions(
    mock_generate_presigned_url,
    event_builder,
    test_s3_bucket,
    filename,
    expected_ext,
    expected_content_type,
):
    """Test presigned URL generation for various supported, case-insensitive file extensions."""
    event = event_builder.api_gateway_proxy_event(query_params={"filename": filename})
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body_data = json.loads(response["body"])
    assert body_data["data"]["filename"] == filename
    assert body_data["data"]["file_extension"] == expected_ext
    assert body_data["data"]["content_type"] == expected_content_type

    call_args = mock_generate_presigned_url.call_args[1]
    assert call_args["content_type"] == expected_content_type


@pytest.mark.parametrize(
    "query_params",
    [
        None,  # Simulates missing queryStringParameters
        {},  # Simulates empty queryStringParameters
        {"other_param": "value"},  # Missing filename
        {"filename": ""},  # Empty filename
    ],
)
def test_lambda_handler_missing_or_invalid_filename(
    event_builder, test_s3_bucket, query_params
):
    """Test 400 error for various missing or invalid filename scenarios."""
    event = event_builder.api_gateway_proxy_event(query_params=query_params)
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert "error" in body_data
    assert body_data["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.parametrize(
    "filename",
    [
        "document.pdf",
        "image.jpg",
        "audio.mp3",
        "text.txt",
        "archive.zip",
        "video.xyz",
        "no_extension",
        "video.",
    ],
)
def test_lambda_handler_invalid_file_extensions(
    event_builder, test_s3_bucket, filename
):
    """Test 400 error for unsupported file extensions."""
    event = event_builder.api_gateway_proxy_event(query_params={"filename": filename})
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert "Invalid video file extension" in body_data["error"]["message"]
    assert ".mp4" in body_data["error"]["message"]


def test_lambda_handler_s3_error(
    mock_generate_presigned_url, event_builder, test_s3_bucket
):
    """Test 500 error handling when S3 presigned URL generation fails."""
    mock_generate_presigned_url.side_effect = Exception("S3 service unavailable")
    event = event_builder.api_gateway_proxy_event(
        query_params={"filename": "test_video.mp4"}
    )

    response = lambda_handler(event, {})

    assert response["statusCode"] == 500
    body_data = json.loads(response["body"])
    assert body_data["error"]["code"] == "INTERNAL_ERROR"


def test_lambda_handler_uuid_in_key_generation(
    mock_generate_presigned_url, event_builder, test_s3_bucket
):
    """Test that a unique UUID is generated in the S3 key for each call."""
    event = event_builder.api_gateway_proxy_event(
        query_params={"filename": "test_video.mp4"}
    )

    # Make multiple calls
    lambda_handler(event, {})
    lambda_handler(event, {})

    assert mock_generate_presigned_url.call_count == 2
    key1 = mock_generate_presigned_url.call_args_list[0][1]["key"]
    key2 = mock_generate_presigned_url.call_args_list[1][1]["key"]

    assert key1 != key2
    assert key1.startswith("uploads/") and key1.endswith("/test_video.mp4")
    assert key2.startswith("uploads/") and key2.endswith("/test_video.mp4")


def test_lambda_handler_cors_headers(
    mock_generate_presigned_url, event_builder, test_s3_bucket
):
    """Test that proper CORS headers are included in both success and error responses."""
    # Test success response
    success_event = event_builder.api_gateway_proxy_event(
        query_params={"filename": "test.mp4"}
    )
    success_response = lambda_handler(success_event, {})
    assert success_response["statusCode"] == 200
    assert "Access-Control-Allow-Origin" in success_response["headers"]

    # Test error response
    error_event = event_builder.api_gateway_proxy_event(
        query_params={"filename": "invalid.txt"}
    )
    error_response = lambda_handler(error_event, {})
    assert error_response["statusCode"] == 400
    assert "Access-Control-Allow-Origin" in error_response["headers"]


def test_lambda_handler_response_structure(
    mock_generate_presigned_url, event_builder, test_s3_bucket
):
    """Test the complete structure of a successful response."""
    event = event_builder.api_gateway_proxy_event(
        query_params={"filename": "test.mp4"}
    )
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body_data = json.loads(response["body"])
    assert "data" in body_data
    assert "metadata" in body_data

    data = body_data["data"]
    required_fields = [
        "presigned_url",
        "filename",
        "file_extension",
        "expires_in_seconds",
        "upload_method",
        "content_type",
    ]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    assert data["upload_method"] == "PUT"
    assert data["content_type"] == "video/mp4"