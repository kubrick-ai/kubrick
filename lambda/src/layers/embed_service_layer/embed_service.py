import os
from typing import BinaryIO, Optional, List, Union, Dict, Any
from twelvelabs import TwelveLabs
from twelvelabs.types import VideoSegment, VideoEmbeddingTask, VideoEmbeddingMetadata
from twelvelabs.embed import (
    TasksStatusResponse,
    TasksRetrieveResponse,
    TasksCreateResponse,
)
from logging import getLogger
from embedding_cache import EmbeddingCache


class EmbedService:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        clip_length: int,
        logger=getLogger(),
        cache_table_name: Optional[str] = None,
    ):
        self.clip_length = clip_length
        self.client = TwelveLabs(api_key=api_key)
        self.model_name = model_name
        self.logger = logger

        # Initialize cache if table name provided
        self.cache = None
        if cache_table_name:
            self.cache = EmbeddingCache(cache_table_name, logger=logger)
            self.logger.info(
                f"Initialized embedding cache with table: {cache_table_name}"
            )
        else:
            self.logger.info("No cache table specified, running without cache")

    def extract_text_embedding(self, input_text: str) -> list[float]:
        # Check cache first if available
        if self.cache:
            cached_embedding = self.cache.get_cached_embedding(
                content_data=input_text,
                model_name=self.model_name,
                clip_length=None,
                embedding_scope=["text"],
            )

            if cached_embedding:
                self.logger.info("Using cached text embedding")
                segments = cached_embedding.get("segments", [])
                if segments and segments[0].get("float"):
                    return segments[0]["float"]

        # Cache miss or no cache - proceed with API call
        self.logger.info("Cache miss - creating new text embedding")
        res = self.client.embed.create(
            model_name=self.model_name, text_truncate="start", text=input_text
        )

        if not (
            res.text_embedding
            and res.text_embedding.segments
            and res.text_embedding.segments[0].float_
        ):
            raise Exception("Could not extract embedding")

        # Cache the result if cache is available
        if self.cache and res.text_embedding:
            self.cache.store_embedding(
                content_data=input_text,
                model_name=self.model_name,
                clip_length=None,
                embedding_scope=["text"],
                video_embedding=res.text_embedding.dict(),
                task_id="text_" + str(abs(hash(input_text))),
            )

        return res.text_embedding.segments[0].float_

    def extract_image_embedding(
        self,
        file: Optional[BinaryIO] = None,
        url: Optional[str] = None,
    ) -> list[float]:
        content_key = url if url else file

        # Check cache first if available
        if self.cache and content_key:
            cached_embedding = self.cache.get_cached_embedding(
                content_data=content_key,
                model_name=self.model_name,
                clip_length=None,
                embedding_scope=["image"],
            )

            if cached_embedding:
                self.logger.info("Using cached image embedding")
                segments = cached_embedding.get("segments", [])
                if segments and segments[0].get("float"):
                    return segments[0]["float"]

        # Cache miss or no cache - proceed with API call
        self.logger.info("Cache miss - creating new image embedding")
        if url:
            res = self.client.embed.create(model_name=self.model_name, image_url=url)
        elif file:
            res = self.client.embed.create(model_name=self.model_name, image_file=file)
        else:
            raise Exception("Expected image file or url as argument")

        if not (
            res.image_embedding
            and res.image_embedding.segments
            and res.image_embedding.segments[0].float_
        ):
            raise Exception("Could not extract embedding")

        # Cache the result if cache is available
        if self.cache and content_key and res.image_embedding:
            self.cache.store_embedding(
                content_data=content_key,
                model_name=self.model_name,
                clip_length=None,
                embedding_scope=["image"],
                video_embedding=res.image_embedding.dict(),
                task_id="image_" + str(abs(hash(str(content_key)))),
            )

        return res.image_embedding.segments[0].float_

    def extract_audio_embedding(
        self,
        file: Optional[BinaryIO] = None,
        url: Optional[str] = None,
    ) -> list[float]:
        content_key = url if url else file

        # Check cache first if available
        if self.cache and content_key:
            cached_embedding = self.cache.get_cached_embedding(
                content_data=content_key,
                model_name=self.model_name,
                clip_length=None,
                embedding_scope=["audio"],
            )

            if cached_embedding:
                self.logger.info("Using cached audio embedding")
                segments = cached_embedding.get("segments", [])
                if segments and segments[0].get("float"):
                    return segments[0]["float"]

        # Cache miss or no cache - proceed with API call
        self.logger.info("Cache miss - creating new audio embedding")
        if url:
            res = self.client.embed.create(model_name=self.model_name, audio_url=url)
        elif file:
            res = self.client.embed.create(model_name=self.model_name, audio_file=file)
        else:
            raise Exception("Expected audio file or url as argument")

        if not (
            res.audio_embedding
            and res.audio_embedding.segments
            and res.audio_embedding.segments[0].float_
        ):
            raise Exception("Could not extract embedding")

        # Cache the result if cache is available
        if self.cache and content_key and res.audio_embedding:
            self.cache.store_embedding(
                content_data=content_key,
                model_name=self.model_name,
                clip_length=None,
                embedding_scope=["audio"],
                video_embedding=res.audio_embedding.dict(),
                task_id="audio_" + str(abs(hash(str(content_key)))),
            )

        return res.audio_embedding.segments[0].float_

    def extract_video_embedding(
        self,
        file: Optional[Union[str, BinaryIO, None]] = None,
        url: Optional[str] = None,
        query_modality: List[str] = ["visual-text"],
        clip_length: Optional[int] = None,
        video_embedding_scope: List[str] = ["clip", "video"],
    ):
        self.logger.info("Extracting video features...")

        clip_length = clip_length or self.clip_length
        content_key = url if url else file

        # Check cache first if available
        if self.cache and content_key:
            cached_embedding = self.cache.get_cached_embedding(
                content_data=content_key,
                model_name=self.model_name,
                clip_length=clip_length,
                embedding_scope=video_embedding_scope,
            )

            if cached_embedding:
                self.logger.info("Using cached video embedding")
                # Extract segments from cached data matching the original format
                segments = cached_embedding.get("segments", [])
                return [
                    segment["embedding"]
                    for segment in segments
                    if segment["scope"] == "video"
                    and segment["modality"] in query_modality
                ]

        # Cache miss or no cache - proceed with API call
        self.logger.info("Cache miss - creating new embedding request")
        embedding_request = self.create_embedding_request(
            url=url,
            file=file,
            clip_length=clip_length,
            video_embedding_scope=video_embedding_scope,
        )

        if not embedding_request.id:
            raise Exception("Embedding request ID is None")

        self._wait_for_request_completion(embedding_request)

        # Get the complete response for caching
        response = self.retrieve_embed_response(embedding_request.id)

        # Get normalized segments
        segments = self.retrieve_segments(embedding_request.id)

        # Cache the normalized segments if cache is available
        if self.cache and content_key:
            normalized_embedding = {
                "segments": segments,
                "metadata": (
                    response.video_embedding.metadata.dict()
                    if response.video_embedding and response.video_embedding.metadata
                    else {}
                ),
            }
            self.cache.store_embedding(
                content_data=content_key,
                model_name=self.model_name,
                clip_length=clip_length,
                embedding_scope=video_embedding_scope,
                video_embedding=normalized_embedding,
                task_id=str(embedding_request.id),
            )

        self.logger.info(f"Extracted video features: {segments}")

        return [
            segment["embedding"]
            for segment in segments
            if segment["scope"] == "video" and segment["modality"] in query_modality
        ]

    def create_embedding_request(
        self,
        *,
        url: Optional[str] = None,
        file: Optional[Union[str, BinaryIO, None]] = None,
        clip_length: Optional[int] = None,
        video_embedding_scope: List[str] = ["clip", "video"],
    ) -> TasksCreateResponse:
        clip_length = clip_length or self.clip_length

        self.logger.info("Creating embedding request...")
        if url:
            embedding_request = self.client.embed.tasks.create(
                model_name=self.model_name,
                video_url=url,
                video_clip_length=clip_length,
                video_embedding_scope=video_embedding_scope,
            )
        elif file:
            embedding_request = self.client.embed.tasks.create(
                model_name=self.model_name,
                video_file=file,
                video_clip_length=clip_length,
                video_embedding_scope=video_embedding_scope,
            )
        else:
            raise Exception("Either file or url must be provided")

        self.logger.info(f"Created embedding request: id={embedding_request.id}")

        return embedding_request

    def _wait_for_request_completion(self, embedding_request: TasksCreateResponse):
        if not embedding_request.id:
            raise Exception("Embedding request ID is None")

        status = self.client.embed.tasks.wait_for_done(
            task_id=embedding_request.id, callback=self._on_request_update
        )
        self.logger.info(f"Embedding done: {status}")

    def retrieve_embed_response(self, task_id: str) -> TasksRetrieveResponse:
        return self.client.embed.tasks.retrieve(
            task_id=task_id, embedding_option=["visual-text", "audio"]
        )

    def retrieve_segments(self, task_id: str) -> List[Dict[str, Any]]:
        res = self.retrieve_embed_response(task_id=task_id)

        if not (
            res.video_embedding
            and res.video_embedding.segments
            and res.video_embedding.segments[0].float_
        ):
            raise Exception("Could not extract embedding")

        segments = res.video_embedding.segments
        self.logger.debug(f"Retrieved segments: {segments}")

        return self.normalize_segments(segments)

    def normalize_segments(self, segments: List[VideoSegment]) -> List[Dict[str, Any]]:
        return [
            {
                "start_time": segment.start_offset_sec,
                "end_time": segment.end_offset_sec,
                "scope": segment.embedding_scope,  # "clip" or "video"
                "modality": segment.embedding_option,  # "text-visual" or "audio"
                "embedding": segment.float_,
            }
            for segment in segments
        ]

    def _on_request_update(self, task: TasksStatusResponse):
        self.logger.debug(f"Status={task.status}")

    def get_embedding_request_status(self, task_id):
        response: TasksStatusResponse = self.client.embed.tasks.status(task_id=task_id)
        return response.status

    def get_video_metadata(
        self, response: TasksRetrieveResponse
    ) -> VideoEmbeddingMetadata | None:
        if response.video_embedding and response.video_embedding.metadata:
            return response.video_embedding.metadata
