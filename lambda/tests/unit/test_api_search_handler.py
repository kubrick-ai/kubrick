import json
import base64
import pytest
from unittest.mock import patch, MagicMock

from api_search_handler.lambda_function import lambda_handler


def create_multipart_form_data(fields):
    """Helper to create a multipart/form-data body for testing."""
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body_parts = []

    for field_name, field_value in fields.items():
        if isinstance(field_value, dict) and "content" in field_value:
            # File field
            content = field_value["content"]
            filename = field_value.get("filename", "test_file")
            content_type = field_value.get("content_type", "application/octet-stream")
            header = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
            body_parts.append(header)
            body_parts.append(
                content.encode("utf-8") if isinstance(content, str) else content
            )
            body_parts.append(b"\r\n")
        else:
            # Text field
            header = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n'
            ).encode("utf-8")
            body_parts.append(header)
            field_data = (
                json.dumps(field_value)
                if isinstance(field_value, (dict, list))
                else str(field_value)
            )
            body_parts.append(field_data.encode("utf-8"))
            body_parts.append(b"\r\n")

    body_parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(body_parts), boundary


@pytest.fixture
def mock_search_controller():
    """Mocks the global search_controller instance in the lambda function."""
    with patch("api_search_handler.lambda_function.search_controller") as mock_service:
        yield mock_service


def test_lambda_handler_text_search_success(mock_search_controller, kubrick_secret):
    """Test successful text search."""
    mock_search_controller.process_search_request.return_value = (
        [{"id": 1, "similarity": 0.85}],
        {"page": 0, "limit": 10, "total": 1},
    )

    body, boundary = create_multipart_form_data(
        {"query_type": "text", "query_text": "test search query", "page_limit": "10"}
    )
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body_data = json.loads(response["body"])
    assert len(body_data["data"]) == 1
    assert body_data["data"][0]["similarity"] == 0.85
    mock_search_controller.process_search_request.assert_called_once_with(event)


def test_lambda_handler_image_search_success(mock_search_controller, kubrick_secret):
    """Test successful image search."""
    mock_search_controller.process_search_request.return_value = (
        [{"id": 2, "similarity": 0.92}],
        {"page": 0, "limit": 5, "total": 1},
    )

    body, boundary = create_multipart_form_data(
        {
            "query_type": "image",
            "page_limit": "5",
            "query_media_file": {
                "content": b"fake_image_data",
                "filename": "test.jpg",
                "content_type": "image/jpeg",
            },
        }
    )
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body_data = json.loads(response["body"])
    assert len(body_data["data"]) == 1
    assert body_data["metadata"]["limit"] == 5


def test_lambda_handler_options_request(kubrick_secret):
    """Test CORS preflight OPTIONS request returns 200 with correct headers."""
    event = {"httpMethod": "OPTIONS"}
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert "POST" in response["headers"]["Access-Control-Allow-Methods"]
    assert "OPTIONS" in response["headers"]["Access-Control-Allow-Methods"]
    assert response["body"] == ""


def test_lambda_handler_search_request_error(mock_search_controller, kubrick_secret):
    """Test 400 error for invalid search parameters."""
    from search_errors import SearchRequestError

    mock_search_controller.process_search_request.side_effect = SearchRequestError(
        "Invalid query parameters"
    )
    body, boundary = create_multipart_form_data({"query_type": "text"})
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert body_data["error"]["code"] == "INVALID_REQUEST"


def test_lambda_handler_embedding_error(mock_search_controller, kubrick_secret):
    """Test 422 error when embedding fails."""
    from search_errors import EmbeddingError

    mock_search_controller.process_search_request.side_effect = EmbeddingError(
        "Failed to extract text embedding"
    )
    body, boundary = create_multipart_form_data(
        {"query_type": "text", "query_text": "test"}
    )
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    response = lambda_handler(event, {})

    assert response["statusCode"] == 422
    body_data = json.loads(response["body"])
    assert body_data["error"]["code"] == "EMBEDDING_ERROR"


def test_lambda_handler_database_error(mock_search_controller, kubrick_secret):
    """Test 503 error when the database is unavailable."""
    from search_errors import DatabaseError

    mock_search_controller.process_search_request.side_effect = DatabaseError(
        "Vector database connection failed"
    )
    body, boundary = create_multipart_form_data(
        {"query_type": "text", "query_text": "test"}
    )
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    response = lambda_handler(event, {})

    assert response["statusCode"] == 503
    body_data = json.loads(response["body"])
    assert body_data["error"]["code"] == "DATABASE_ERROR"


def test_lambda_handler_unexpected_error(mock_search_controller, kubrick_secret):
    """Test 500 for unexpected runtime errors."""
    mock_search_controller.process_search_request.side_effect = RuntimeError(
        "Unexpected system error"
    )
    body, boundary = create_multipart_form_data(
        {"query_type": "text", "query_text": "test"}
    )
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    response = lambda_handler(event, {})

    assert response["statusCode"] == 500
    body_data = json.loads(response["body"])
    assert body_data["error"]["code"] == "INTERNAL_ERROR"


def test_lambda_handler_media_processing_error(mock_search_controller, kubrick_secret):
    """Test 422 error when media processing fails."""
    from search_errors import MediaProcessingError

    mock_search_controller.process_search_request.side_effect = MediaProcessingError(
        "Failed to process uploaded media file"
    )
    body, boundary = create_multipart_form_data(
        {
            "query_type": "image",
            "query_media_file": {
                "content": b"invalid_image_data",
                "filename": "test.jpg",
                "content_type": "image/jpeg",
            },
        }
    )
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    response = lambda_handler(event, {})

    assert response["statusCode"] == 422
    body_data = json.loads(response["body"])
    assert body_data["error"]["code"] == "MEDIA_PROCESSING_ERROR"


def test_lambda_handler_search_error(mock_search_controller, kubrick_secret):
    """Test 500 error for generic search errors."""
    from search_errors import SearchError

    mock_search_controller.process_search_request.side_effect = SearchError(
        "Generic search service error"
    )
    body, boundary = create_multipart_form_data(
        {"query_type": "text", "query_text": "test"}
    )
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    response = lambda_handler(event, {})

    assert response["statusCode"] == 500
    body_data = json.loads(response["body"])
    assert body_data["error"]["code"] == "INTERNAL_ERROR"


def test_lambda_handler_validation_error(mock_search_controller, kubrick_secret):
    """Test 400 error for Pydantic validation failures."""
    from pydantic import ValidationError

    # Create a ValidationError using the correct InitErrorDetails structure
    from pydantic_core import InitErrorDetails

    error_details: list[InitErrorDetails] = [
        {
            "type": "missing",
            "loc": ("query_text",),
            "input": {},
        }
    ]
    mock_search_controller.process_search_request.side_effect = (
        ValidationError.from_exception_data("ValidationError", error_details)
    )
    body, boundary = create_multipart_form_data({"query_type": "text"})
    event = {
        "httpMethod": "POST",
        "headers": {"Content-Type": f"multipart/form-data; boundary={boundary}"},
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True,
    }

    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body_data = json.loads(response["body"])
    assert body_data["error"]["code"] == "VALIDATION_ERROR"
    assert "Invalid request format" in body_data["error"]["message"]
