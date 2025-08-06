import sys
import os
import boto3
import json
import pytest
from moto import mock_aws
from unittest.mock import MagicMock, patch
from mock_data import EventBuilder, TestDataBuilder


# ============================================================================
# CONFIGURATION
# ============================================================================


class TestConfig:
    """Configuration for test environment setup."""

    # Layer configuration
    LAYERS = [
        "response_utils_layer",
        "vector_database_layer",
        "s3_utils_layer",
        "config_layer",
        "embed_service_layer",
    ]

    # Lambda source directories
    LAMBDA_SOURCES = [
        "api_fetch_videos_handler",
        "api_fetch_tasks",
        "api_search_handler",
        "api_video_upload_link_handler",
        "s3_delete_handler",
        "sqs_embedding_task_consumer",
        "sqs_embedding_task_producer",
    ]

    # Default environment variables
    ENV = {
        # AWS Credentials
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "AWS_DEFAULT_REGION": "us-east-1",
        # Lambda Env Vars
        "SECRET_NAME": "kubrick_secret",
        "QUEUE_URL": "https://test-queue-url-placeholder",
        "PRESIGNED_URL_EXPIRY": "3600",
        "S3_BUCKET_NAME": "test-bucket",
    }

    # External modules to mock
    EXTERNAL_MODULES = [
        "twelvelabs",
    ]


def setup_python_paths():
    """Setup Python paths for Lambda layers and source code."""
    test_dir = os.path.dirname(__file__)

    # Path to layers
    layers_dir = os.path.abspath(os.path.join(test_dir, "../../src/layers"))
    layer_paths = [os.path.join(layers_dir, layer) for layer in TestConfig.LAYERS]

    # Lambda source paths
    src_dir = os.path.abspath(os.path.join(test_dir, "../../src"))
    src_paths = [src_dir] + [
        os.path.join(src_dir, source) for source in TestConfig.LAMBDA_SOURCES
    ]

    # Add all paths to sys.path
    for path in layer_paths + src_paths:
        if path not in sys.path:
            sys.path.insert(0, path)


def setup_module_mocks():
    """Mock external modules that may not be available in test environment."""
    for module_name in TestConfig.EXTERNAL_MODULES:
        if module_name == "twelvelabs":
            mock_twelvelabs = MagicMock()
            mock_types = MagicMock()
            mock_embed = MagicMock()

            sys.modules["twelvelabs"] = mock_twelvelabs
            sys.modules["twelvelabs.types"] = mock_types
            sys.modules["twelvelabs.embed"] = mock_embed
        else:
            sys.modules[module_name] = MagicMock()

    # Mock VectorDBService to prevent database connections during import
    mock_vector_db_service = MagicMock()
    sys.modules["vector_db_service"] = MagicMock()
    sys.modules["vector_db_service"].VectorDBService = mock_vector_db_service
    
    # Mock config module functions used at module level
    mock_config = MagicMock()
    mock_config.get_secret.return_value = TestDataBuilder.kubrick_secret()
    mock_config.get_db_config.return_value = {"host": "test", "user": "test"}
    sys.modules["config"] = mock_config


def setup_env():
    """Setup test environment variables."""
    for var, value in TestConfig.ENV.items():
        os.environ[var] = value


# Create a single mock_aws instance to be used for the entire test session
mock_aws_instance = mock_aws()


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest file
    after command line options have been parsed.
    """
    # Start the mock before any tests are collected
    mock_aws_instance.start()

    # Setup environment variables
    setup_env()

    # Create the secret that some modules expect at import time
    # This must be done after the mock is started and envs are set
    sm_client = boto3.client(
        "secretsmanager", region_name=TestConfig.ENV["AWS_DEFAULT_REGION"]
    )
    secret_name = TestConfig.ENV["SECRET_NAME"]
    secret_value = TestDataBuilder.kubrick_secret()
    sm_client.create_secret(Name=secret_name, SecretString=json.dumps(secret_value))

    # Setup paths and mocks after envs are ready
    setup_python_paths()
    setup_module_mocks()


def pytest_unconfigure(config):
    """
    Called before test process is exited.
    """
    # Stop the mock after all tests are finished
    mock_aws_instance.stop()


# ============================================================================
# AWS SERVICE FIXTURES
# ============================================================================


@pytest.fixture
def secrets_manager():
    """Provide a clean Secrets Manager client for each test."""
    return boto3.client("secretsmanager")


@pytest.fixture
def sqs_client():
    """Provide a clean SQS client for each test."""
    return boto3.client("sqs")


@pytest.fixture
def s3_client():
    """Provide a clean S3 client for each test."""
    return boto3.client("s3")


@pytest.fixture
def kubrick_secret(secrets_manager):
    """
    Fetches the 'kubrick_secret' value.
    Note: The secret is created in pytest_configure to be available at import time.
    This fixture ensures test isolation by re-creating it for each test if needed,
    but primarily serves to provide the secret data to the test function.
    """
    secret_name = os.environ.get("SECRET_NAME")
    try:
        # In case a test modifies and deletes the secret, we ensure it exists.
        secrets_manager.describe_secret(SecretId=secret_name)
    except secrets_manager.exceptions.ResourceNotFoundException:
        secret_value = TestDataBuilder.kubrick_secret()
        secrets_manager.create_secret(
            Name=secret_name, SecretString=json.dumps(secret_value)
        )

    response = secrets_manager.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])


@pytest.fixture
def test_sqs_queue(sqs_client):
    """Create a test SQS queue and return its URL."""
    queue_response = sqs_client.create_queue(QueueName="test-queue")
    queue_url = queue_response["QueueUrl"]

    # Set the environment variable that Lambda functions expect
    with patch.dict(os.environ, {"QUEUE_URL": queue_url}):
        yield queue_url


@pytest.fixture
def test_s3_bucket(s3_client):
    """Create a test S3 bucket."""
    bucket_name = os.environ.get("S3_BUCKET_NAME")
    s3_client.create_bucket(Bucket=bucket_name)
    return bucket_name


# ============================================================================
# BUILDER FIXTURES
# ============================================================================


@pytest.fixture
def event_builder():
    """Provide the EventBuilder class for comprehensive event creation."""
    return EventBuilder


@pytest.fixture
def test_data_builder():
    """Provide the TestDataBuilder class for creating test data."""
    return TestDataBuilder
