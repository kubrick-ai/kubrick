import json
import hashlib
import time
from typing import Optional, Dict, Any
from logging import getLogger
import boto3
from botocore.exceptions import ClientError


class EmbeddingCache:
    def __init__(self, table_name: str, ttl_days: int = 30, logger=getLogger()):
        self.table_name = table_name
        self.ttl_days = ttl_days
        self.logger = logger
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(table_name)  # type: ignore

    def _generate_content_hash(self, content_data: Any) -> str:
        """Generate SHA256 hash of content for cache key"""
        if hasattr(content_data, 'read'):  # File-like object (BytesIO, etc.)
            # Read the content, hash it, then reset position
            current_pos = content_data.tell() if hasattr(content_data, 'tell') else 0
            content_data.seek(0)
            content_bytes = content_data.read()
            if hasattr(content_data, 'seek'):
                content_data.seek(current_pos)  # Reset to original position
            return hashlib.sha256(content_bytes).hexdigest()
        elif isinstance(content_data, (bytes, bytearray)):
            # Direct binary data
            return hashlib.sha256(content_data).hexdigest()
        else:
            # String or other JSON-serializable content
            content_str = json.dumps(content_data, sort_keys=True)
            return hashlib.sha256(content_str.encode()).hexdigest()

    def _generate_embedding_config(
        self, model_name: str, clip_length: Optional[int], embedding_scope: list
    ) -> str:
        """Generate embedding configuration string for cache key"""
        scope_str = ",".join(sorted(embedding_scope))
        clip_str = str(clip_length) if clip_length is not None else "none"
        return f"{model_name}:{clip_str}:{scope_str}"

    def _calculate_expires_at(self) -> int:
        """Calculate TTL expiration timestamp"""
        return int(time.time()) + (self.ttl_days * 24 * 60 * 60)

    def get_cached_embedding(
        self,
        content_data: Any,
        model_name: str,
        clip_length: Optional[int],
        embedding_scope: list,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached embedding from DynamoDB

        Args:
            content_data: Content to hash (file content, URL, etc.)
            model_name: Embedding model name
            clip_length: Video clip length
            embedding_scope: List of embedding scopes

        Returns:
            Cached video_embedding object or None if not found
        """
        try:
            content_hash = self._generate_content_hash(content_data)
            embedding_config = self._generate_embedding_config(
                model_name, clip_length, embedding_scope
            )

            self.logger.info(
                f"Checking cache for content_hash={content_hash[:8]}... config={embedding_config}"
            )

            response = self.table.get_item(
                Key={"content_hash": content_hash, "embedding_config": embedding_config}
            )

            if "Item" in response:
                item = response["Item"]

                # Update access tracking
                self._update_access_tracking(content_hash, embedding_config)

                self.logger.info(f"Cache hit for content_hash={content_hash[:8]}...")
                # Parse JSON string back to dict
                return json.loads(item["video_embedding"])
            else:
                self.logger.info(f"Cache miss for content_hash={content_hash[:8]}...")
                return None

        except ClientError as e:
            self.logger.error(f"Error reading from DynamoDB cache: {e}")
            return None

    def store_embedding(
        self,
        content_data: Any,
        model_name: str,
        clip_length: Optional[int],
        embedding_scope: list,
        video_embedding: Dict[str, Any],
        task_id: str,
    ) -> bool:
        """
        Store embedding in DynamoDB cache

        Args:
            content_data: Content to hash (file content, URL, etc.)
            model_name: Embedding model name
            clip_length: Video clip length
            embedding_scope: List of embedding scopes
            video_embedding: Complete video_embedding object from API
            task_id: TwelveLabs task ID for reference

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            content_hash = self._generate_content_hash(content_data)
            embedding_config = self._generate_embedding_config(
                model_name, clip_length, embedding_scope
            )
            current_time = int(time.time())

            item = {
                "content_hash": content_hash,
                "embedding_config": embedding_config,
                "task_id": task_id,
                "video_embedding": json.dumps(video_embedding),  # Store as JSON string
                "created_at": current_time,
                "expires_at": self._calculate_expires_at(),
                "last_accessed": current_time,
                "access_count": 1,
            }

            self.table.put_item(Item=item)
            self.logger.info(
                f"Stored embedding in cache: content_hash={content_hash[:8]}... config={embedding_config}"
            )
            return True

        except ClientError as e:
            self.logger.error(f"Error storing in DynamoDB cache: {e}")
            return False

    def _update_access_tracking(self, content_hash: str, embedding_config: str):
        """Update last_accessed and increment access_count"""
        try:
            self.table.update_item(
                Key={
                    "content_hash": content_hash,
                    "embedding_config": embedding_config,
                },
                UpdateExpression="SET last_accessed = :timestamp ADD access_count :inc",
                ExpressionAttributeValues={":timestamp": int(time.time()), ":inc": 1},
            )
        except ClientError as e:
            self.logger.warning(f"Failed to update access tracking: {e}")

