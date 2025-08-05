import json
import pytest
from unittest.mock import patch, MagicMock

from api_fetch_tasks_handler.lambda_function import lambda_handler


@pytest.fixture
def mock_vector_db():
    """Mocks VectorDBService and returns its mock instance."""
    with patch("api_fetch_tasks_handler.lambda_function.VectorDBService") as mock_service:
        mock_instance = MagicMock()
        mock_service.return_value = mock_instance
        yield mock_instance


def test_lambda_handler_success(mock_vector_db, kubrick_secret, event_builder):
    """Test successful retrieval of tasks with valid pagination."""
    mock_vector_db.fetch_tasks.return_value = (
        [
            {
                "id": 1,
                "sqs_message_id": "msg-123",
                "s3_bucket": "test-bucket",
                "s3_key": "test-key.mp4",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "status": "completed",
            }
        ],
        1,
    )

    event = event_builder.api_gateway_proxy_event(
        query_params={"limit": "5", "page": "1"}
    )
    response = lambda_handler(event, {})

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


def test_lambda_handler_default_params(mock_vector_db, kubrick_secret, event_builder):
    """Test that default parameters are used when none are provided."""
    mock_vector_db.fetch_tasks.return_value = ([], 0)

    event = event_builder.api_gateway_proxy_event()
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["metadata"]["limit"] == 10  # Default limit from lambda
    assert body["metadata"]["page"] == 0    # Default page from lambda
    mock_vector_db.fetch_tasks.assert_called_once_with(page=0, limit=10)


def test_lambda_handler_limit_validation(mock_vector_db, kubrick_secret, event_builder):
    """Test that pagination parameters are capped and floored correctly."""
    mock_vector_db.fetch_tasks.return_value = ([], 0)

    event = event_builder.api_gateway_proxy_event(
        query_params={"limit": "100", "page": "-5"}
    )
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["metadata"]["limit"] == 50  # Capped at MAX_TASK_LIMIT
    assert body["metadata"]["page"] == 0    # Min value is 0
    mock_vector_db.fetch_tasks.assert_called_once_with(page=0, limit=50)


def test_lambda_handler_invalid_params(mock_vector_db, kubrick_secret, event_builder):
    """Test for a 400 validation error with invalid string parameters."""
    event = event_builder.api_gateway_proxy_event(
        query_params={"limit": "invalid", "page": "also_invalid"}
    )
    response = lambda_handler(event, {})

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"
    mock_vector_db.fetch_tasks.assert_not_called()


def test_lambda_handler_database_error(mock_vector_db, kubrick_secret, event_builder):
    """Test for a 500 internal server error when the database fails."""
    mock_vector_db.fetch_tasks.side_effect = Exception("Database connection failed")

    event = event_builder.api_gateway_proxy_event()
    response = lambda_handler(event, {})

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert "error" in body
    assert body["error"]["message"] == "Internal server error"


def test_lambda_handler_secrets_error(event_builder):
    """Test that an exception is raised if secrets retrieval fails."""
    with patch("api_fetch_tasks_handler.lambda_function.get_secret") as mock_get_secret:
        mock_get_secret.side_effect = Exception("Failed to retrieve secret")
        event = event_builder.api_gateway_proxy_event()

        with pytest.raises(Exception, match="Failed to retrieve secret"):
            lambda_handler(event, {})


def test_lambda_handler_boundary_conditions(
    mock_vector_db, kubrick_secret, event_builder
):
    """Test that a limit of 0 is corrected to the minimum of 1."""
    mock_vector_db.fetch_tasks.return_value = ([], 0)

    event = event_builder.api_gateway_proxy_event(
        query_params={"limit": "0", "page": "0"}
    )
    response = lambda_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["metadata"]["limit"] == 1  # Minimum enforced
    mock_vector_db.fetch_tasks.assert_called_once_with(page=0, limit=1)
