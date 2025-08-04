from typing import BinaryIO, Optional, List, Union
from twelvelabs import TwelveLabs
from twelvelabs.types import VideoSegment, VideoEmbeddingTask, VideoEmbeddingMetadata
from twelvelabs.embed import TasksStatusResponse, TasksRetrieveResponse
from logging import getLogger


class EmbedService:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        clip_length: int,
        logger=getLogger(),
    ):
        self.clip_length = clip_length
        self.client = TwelveLabs(api_key=api_key)
        self.model_name = model_name
        self.logger = logger

    def extract_text_embedding(self, input_text: str) -> list[float]:
        res = self.client.embed.create(
            model_name=self.model_name, text_truncate="start", text=input_text
        )

        if not (
            res.text_embedding
            and res.text_embedding.segments
            and res.text_embedding.segments[0].float_
        ):
            raise Exception("Could not extract embedding")

        return res.text_embedding.segments[0].float_

    def extract_image_embedding(
        self,
        file: Optional[BinaryIO] = None,
        url: Optional[str] = None,
    ) -> list[float]:
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

        return res.image_embedding.segments[0].float_

    def extract_audio_embedding(
        self,
        file: Optional[BinaryIO] = None,
        url: Optional[str] = None,
    ) -> list[float]:
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

        return res.audio_embedding.segments[0].float_

    def extract_video_embedding(
        self,
        file: Optional[Union[str, BinaryIO, None]] = None,
        url: Optional[str] = None,
        query_modality: List[str] = ["visual-text"],
        clip_length: Optional[int] = None,
    ):
        self.logger.info("Extracting video features...")

        embedding_request = self.create_embedding_request(
            url=url, file=file, clip_length=clip_length
        )

        self._wait_for_request_completion(embedding_request)
        segments = self.retrieve_segments(embedding_request.id)

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
    ) -> VideoEmbeddingTask:
        clip_length = clip_length or self.clip_length

        self.logger.info("Creating embedding request...")
        if url:
            embedding_request = self.client.embed.tasks.create(
                model_name=self.model_name,
                video_url=url,
                video_clip_length=clip_length,
                video_embedding_scope=["clip", "video"],
            )
        elif file:
            embedding_request = self.client.embed.tasks.create(
                model_name=self.model_name,
                video_file=file,
                video_clip_length=clip_length,
                video_embedding_scope=["clip", "video"],
            )
        else:
            raise Exception("Either file or url must be provided")

        self.logger.info(f"Created embedding request: id={embedding_request.id}")

        return embedding_request

    def _wait_for_request_completion(self, embedding_request: VideoEmbeddingTask):
        status = self.client.embed.tasks.wait_for_done(
            task_id=embedding_request.id, callback=self._on_request_update
        )
        self.logger.info(f"Embedding done: {status}")

    def retrieve_embed_response(self, task_id: int) -> TasksRetrieveResponse:
        return self.client.embed.tasks.retrieve(
            task_id=task_id, embedding_option=["visual-text", "audio"]
        )

    def retrieve_segments(self, task_id: int) -> List[VideoSegment]:
        res = self.retrieve_embed_response(task_id=task_id)

        if not (
            res.video_embedding
            and res.video_embedding.segments
            and res.video_embedding.segments[0].float_
        ):
            raise Exception("Could not extract embedding")

        segments = res.video_embedding.segments
        self.logger.info(f"Retrieved segments: {segments}")

        return self.normalize_segments(segments)

    def normalize_segments(self, segments: List[VideoSegment]):
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

    def _on_request_update(self, task: VideoEmbeddingTask):
        self.logger.info(f"Status={task.status}")

    def get_embedding_request_status(self, task_id):
        response: TasksStatusResponse = self.client.embed.tasks.status(task_id=task_id)
        return response.status

    def get_video_metadata(
        self, response: TasksRetrieveResponse
    ) -> VideoEmbeddingMetadata | None:
        if response.video_embedding and response.video_embedding.metadata:
            return response.video_embedding.metadata
