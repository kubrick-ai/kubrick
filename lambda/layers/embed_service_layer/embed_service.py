from typing import BinaryIO, Optional, List, Union
from twelvelabs import TwelveLabs
from twelvelabs.embed import TasksCreateResponse
from twelvelabs.types import VideoSegment, VideoEmbeddingTask, EmbeddingResponse
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

    def extract_text_embedding(self, input_text: str):
        res = self.client.embed.create(
            model_name=self.model_name, text_truncate="start", text=input_text
        )

        if res.text_embedding is not None and res.text_embedding.segments is not None:
            return res.text_embedding.segments[0].float_

    def extract_image_embedding(
        self,
        file: Optional[BinaryIO] = None,
        url: Optional[str] = None,
    ):
        if url:
            res = self.client.embed.create(
                model_name="Marengo-retrieval-2.7", image_url=url
            )
        elif file:
            res = self.client.embed.create(
                model_name="Marengo-retrieval-2.7", image_file=file
            )
        else:
            raise Exception("Expected image file or url as argument")

        if res.image_embedding is not None and res.image_embedding.segments is not None:
            return res.image_embedding.segments[0].float_

    def extract_video_embedding(
        self,
        file: Optional[Union[str, BinaryIO, None]] = None,
        url: Optional[str] = None,
        query_modality: List[str] = ["visual-text"],
    ):
        self.logger.info("Extracting video features...")
        segments = self.extract_video_features(file, url)
        self.logger.info(f"Extracted video features: {segments}")

        return [
            segment["embedding"]
            for segment in segments
            if segment["scope"] == "video" and segment["modality"] in query_modality
        ]

    def extract_video_features(
        self,
        file: Optional[Union[str, BinaryIO, None]],
        url: Optional[str] = None,
        clip_length: Optional[int] = None,
        start_offset: Optional[float] = None,
        end_offset: Optional[float] = None,
    ):
        embedding_request = self.create_embedding_request(
            file, url, clip_length, start_offset, end_offset
        )
        self._wait_for_request_completion(embedding_request.id)
        segments = self._retrieve_segments(embedding_request)
        return self._normalize_segments(segments)

    def create_embedding_request(
        self,
        file: Optional[Union[str, BinaryIO, None]],
        url: Optional[str],
        clip_length: Optional[int],
    ) -> TasksCreateResponse:
        clip_length = clip_length or self.clip_length

        self.logger.info("Creating embedding request...")
        embedding_request = self.client.embed.tasks.create(
            model_name=self.model_name,
            video_file=file,
            video_url=url,
            video_clip_length=clip_length,
            video_embedding_scope=["clip", "video"],
        )

        self.logger.info(
            f"Created embedding request: id={embedding_request.id} model_name={embedding_request.model_name} status={embedding_request.status}"
        )

        return embedding_request

    def _wait_for_request_completion(self, embedding_request):
        status = self.client.embed.tasks.wait_for_done(
            task_id=embedding_request.id, callback=self._on_request_update
        )
        self.logger.info(f"Embedding done: {status}")

    def _retrieve_segments(
        self, embedding_request: VideoEmbeddingTask
    ) -> List[VideoSegment]:
        task = self.client.embed.tasks.retrieve(
            task_id=embedding_request.id, embedding_option=["visual-text", "audio"]
        )

        if not task.video_embedding or not task.video_embedding.segments:
            raise Exception("Embedding failed")

        segments = task.video_embedding.segments
        self.logger.info(f"Retrieved segments: {segments}")

        return segments.video_embedding.segments

    def _normalize_segments(self, segments: List[VideoSegment]):
        result = []
        for segment in segments:
            result.append(
                {
                    "start_time": segment.start_offset_sec,
                    "end_time": segment.end_offset_sec,
                    "scope": segment.embedding_scope,  # "clip" or "video"
                    "modality": segment.embedding_option,  # "text-visual" or "audio"
                    "embedding": segment.float_,
                }
            )
        return result

    def _on_request_update(self, task: VideoEmbeddingTask):
        self.logger.info(f"  Status={task.status}")
