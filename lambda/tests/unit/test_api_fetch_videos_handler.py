import json
import pytest
from unittest.mock import patch, MagicMock

from api_fetch_videos_handler.lambda_function import lambda_handler


@pytest.fixture
def mock_vector_db():
    """Mocks the vector_db instance that was created at module level."""
    with patch("api_fetch_videos_handler.lambda_function.vector_db") as mock_instance:
        yield mock_instance


@pytest.fixture
def mock_add_presigned_urls():
    """Mocks the add_presigned_urls utility function."""
    with patch(
        "api_fetch_videos_handler.lambda_function.add_presigned_urls"
    ) as mock_func:
        yield mock_func


@pytest.fixture
def mock_get_secret():
    """Mocks the get_secret utility function."""
    with patch("api_fetch_videos_handler.lambda_function.get_secret") as mock_func:
        yield mock_func


def test_lambda_handler_success(
    mock_vector_db,
    mock_add_presigned_urls,
    kubrick_secret,
    event_builder,
    test_data_builder,
):
    """Test successful retrieval of a list of videos."""
    # Setup mocks
    videos = [test_data_builder.video()]
    mock_vector_db.fetch_videos.return_value = (videos, 1)

    # Test event
    event = event_builder.api_gateway_proxy_event(
        query_params={"limit": "10", "page": "0"}
    )
    context = {}

    # Execute
    response = lambda_handler(event, context)

    # Assert
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


def test_lambda_handler_default_params(mock_vector_db, kubrick_secret, event_builder):
    """Test that default pagination parameters are used when none are provided."""
    # Setup mock
    mock_vector_db.fetch_videos.return_value = ([], 0)

    # Test event (no query params)
    event = event_builder.api_gateway_proxy_event()
    context = {}

    # Execute
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["metadata"]["limit"] == 12
    assert body["metadata"]["page"] == 0

    mock_vector_db.fetch_videos.assert_called_once_with(page=0, limit=12)


def test_lambda_handler_database_error(mock_vector_db, kubrick_secret, event_builder):
    """Test 500 error response when the database service fails."""
    # Setup mock
    mock_vector_db.fetch_videos.side_effect = Exception("Database connection failed")

    # Test event
    event = event_builder.api_gateway_proxy_event()
    context = {}

    # Execute
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "error" in body
    assert body["error"]["message"] == "Internal server error"


def test_lambda_handler_invalid_params(mock_vector_db, kubrick_secret, event_builder):
    """Test 400 error response for invalid pagination parameters."""
    # Setup mock
    mock_vector_db.fetch_videos.return_value = ([], 0)

    # Test event
    event = event_builder.api_gateway_proxy_event(
        query_params={"limit": "invalid", "page": "also_invalid"}
    )
    context = {}

    # Execute
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    assert "Invalid parameters" in body["error"]["message"]


def test_lambda_handler_with_environment_variables(
    mock_get_secret,
    mock_vector_db,
    mock_add_presigned_urls,
    kubrick_secret,
    event_builder,
):
    """Test that environment variables for secrets and S3 are used correctly."""
    # Setup mocks
    mock_vector_db.fetch_videos.return_value = ([], 0)
    mock_get_secret.return_value = kubrick_secret

    # Test event
    event = event_builder.api_gateway_proxy_event()
    context = {}

    # Execute
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 200
    mock_add_presigned_urls.assert_called_once_with([], 3600)


def test_lambda_handler_no_videos_found(mock_vector_db, kubrick_secret, event_builder):
    """Test successful response with an empty data array when no videos are found."""
    # Setup mock
    mock_vector_db.fetch_videos.return_value = ([], 0)

    # Test event
    event = event_builder.api_gateway_proxy_event(
        query_params={"limit": "10", "page": "0"}
    )
    context = {}

    # Execute
    response = lambda_handler(event, context)

    # Assert
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body["data"]) == 0
    assert body["metadata"]["total"] == 0
    mock_vector_db.fetch_videos.assert_called_once_with(page=0, limit=10)
