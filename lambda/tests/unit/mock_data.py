import json
from typing import Dict, Any, Optional


class EventBuilder:
    """Factory class for creating AWS Lambda test events."""

    @staticmethod
    def s3_event(
        bucket_name: str,
        object_key: str,
        event_name: str = "ObjectCreated:Put",
        region: str = "us-east-1",
    ) -> Dict[str, Any]:
        """Create an S3 event for testing Lambda functions.

        Args:
            bucket_name: S3 bucket name
            object_key: S3 object key
            event_name: S3 event type (default: ObjectCreated:Put)
            region: AWS region (default: us-east-1)

        Returns:
            Dict containing S3 event structure
        """
        return {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": region,
                    "eventTime": "2023-01-01T00:00:00.000Z",
                    "eventName": event_name,
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "bucket": {
                            "name": bucket_name,
                            "arn": f"arn:aws:s3:::{bucket_name}",
                        },
                        "object": {"key": object_key, "size": 1024},
                    },
                }
            ]
        }

    @staticmethod
    def sqs_event_record(
        message_id: str,
        s3_bucket: str,
        s3_key: str,
        tl_task_id: Optional[str] = None,
        region: str = "us-east-1",
    ) -> Dict[str, Any]:
        """Create a single SQS event record for testing.

        Args:
            message_id: SQS message ID
            s3_bucket: S3 bucket name in message body
            s3_key: S3 key in message body
            tl_task_id: Optional TwelveLabs task ID
            region: AWS region (default: us-east-1)

        Returns:
            Dict containing SQS event record structure
        """
        body = {
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
        }
        if tl_task_id:
            body["twelvelabs_video_embedding_task_id"] = tl_task_id

        return {
            "messageId": message_id,
            "receiptHandle": f"receipt-handle-{message_id}",
            "body": json.dumps(body),
            "attributes": {},
            "messageAttributes": {},
            "md5OfBody": "",
            "eventSource": "aws:sqs",
            "eventSourceARN": f"arn:aws:sqs:{region}:123456789012:test-queue",
            "awsRegion": region,
        }

    @staticmethod
    def sqs_event(records: list) -> Dict[str, Any]:
        """Create an SQS event with multiple records.

        Args:
            records: List of SQS event records

        Returns:
            Dict containing SQS event structure
        """
        return {"Records": records}

    @staticmethod
    def api_gateway_proxy_event(
        query_params: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        http_method: str = "GET",
    ) -> Dict[str, Any]:
        """Create an API Gateway proxy event for testing.

        Args:
            query_params: Dictionary of query string parameters
            body: Dictionary for the request body (will be JSON serialized)
            http_method: The HTTP method (e.g., "GET", "POST")

        Returns:
            Dict containing API Gateway proxy event structure
        """
        return {
            "httpMethod": http_method,
            "queryStringParameters": query_params or {},
            "body": json.dumps(body) if body else None,
            "headers": {"Content-Type": "application/json"},
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "api-id",
                "httpMethod": http_method,
                "requestId": "request-id",
                "stage": "prod",
            },
            "isBase64Encoded": False,
        }


class TestDataBuilder:
    """Factory class for creating common test data structures."""

    @staticmethod
    def video(
        id: int = 1,
        filename: str = "test.mp4",
        s3_bucket: str = "test-bucket",
        s3_key: str = "test-key",
        duration: float = 120.5,
        created_at: str = "2023-01-01T00:00:00",
        updated_at: str = "2023-01-01T00:00:00",
        height: int = 720,
        width: int = 1280,
    ) -> Dict[str, Any]:
        """Create a video record dictionary for testing."""
        return {
            "id": id,
            "filename": filename,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
            "duration": duration,
            "created_at": created_at,
            "updated_at": updated_at,
            "height": height,
            "width": width,
        }

    @staticmethod
    def video_metadata(
        filename: str = "test_video.mp4",
        duration: int = 120,
        s3_bucket: str = "test-bucket",
        s3_key: str = "videos/test_video.mp4",
        height: Optional[int] = None,
        width: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create video metadata for testing.

        Args:
            filename: Video filename
            duration: Duration in seconds
            s3_bucket: S3 bucket name
            s3_key: S3 object key
            height: Optional video height
            width: Optional video width

        Returns:
            Dict containing video metadata
        """
        metadata = {
            "filename": filename,
            "duration": duration,
            "s3_bucket": s3_bucket,
            "s3_key": s3_key,
        }

        if height is not None:
            metadata["height"] = height
        if width is not None:
            metadata["width"] = width

        return metadata

    @staticmethod
    def embedding_segment(
        start_time: float = 0,
        end_time: float = 5,
        scope: str = "clip",
        modality: str = "text-visual",
        embedding: list | None = None,
    ) -> Dict[str, Any]:
        """Create an embedding segment for testing.

        Args:
            start_time: Segment start time in seconds
            end_time: Segment end time in seconds
            scope: Embedding scope (clip, video, etc.)
            modality: Embedding modality (text-visual, etc.)
            embedding: Embedding vector (defaults to [0.1, 0.2])

        Returns:
            Dict containing embedding segment
        """
        if embedding is None:
            embedding = [0.1, 0.2]

        return {
            "start_time": start_time,
            "end_time": end_time,
            "scope": scope,
            "modality": modality,
            "embedding": embedding,
        }

    @staticmethod
    def kubrick_secret(
        api_key: str = "test_api_key_12345",
        db_username: str = "test_user",
        db_password: str = "test_password",
    ) -> Dict[str, str]:
        """Create Kubrick secret data for testing.

        Args:
            api_key: TwelveLabs API key
            db_username: Database username
            db_password: Database password

        Returns:
            Dict containing secret values
        """
        return {
            "TWELVELABS_API_KEY": api_key,
            "DB_USERNAME": db_username,
            "DB_PASSWORD": db_password,
        }

