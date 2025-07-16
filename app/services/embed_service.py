from twelvelabs import TwelveLabs
from typing import List, Optional, BinaryIO
from twelvelabs.models.embed import EmbeddingsTask
from app.config import Config


class EmbedService:
    def __init__(self, config=Config()):
        self.config = config
        self.api_key = config.TWELVELABS_API_KEY
        self.client = TwelveLabs(api_key=self.api_key)

    def _on_task_update(self, task: EmbeddingsTask):
        print(f"  Status={task.status}")

    def print_segments(self, segments, max_elements: int = 5):
        for segment in segments:
            print(
                f"  embedding_scope={segment["scope"]} embedding_modality={segment["modality"]} start_time={segment["start_time"]} end_time={segment["end_time"]}"
            )
            if segment["embedding"] is not None:
                print(f"  embeddings: {segment["embedding"][:max_elements]}")

    def extract_video_features(
        self,
        filepath: Optional[str] = None,
        url: Optional[str] = None,
        clip_length: Optional[int] = None,
        start_offset: Optional[float] = None,
        end_offset: Optional[float] = None,
    ):
        task = self._create_embedding_task(
            filepath, url, clip_length, start_offset, end_offset
        )
        self._wait_for_task_completion(task)
        task = self._retrieve_embedding(task)
        return self._process_segments(task)

    def _create_embedding_task(
        self,
        filepath: Optional[str],
        url: Optional[str],
        clip_length: Optional[int],
        start_offset: Optional[float],
        end_offset: Optional[float],
    ):
        clip_length = clip_length or self.config.DEFAULT_CLIP_LENGTH

        task = self.client.embed.task.create(
            model_name=self.config.EMBEDDING_MODEL_NAME,
            video_file=filepath,
            video_url=url,
            video_clip_length=clip_length,
            video_start_offset_sec=start_offset,
            video_end_offset_sec=end_offset,
            video_embedding_scopes=["clip", "video"],
        )

        if self.config.DEBUG:
            print(
                f"Created task: id={task.id} model_name={task.model_name} status={task.status}"
            )

        return task

    def _wait_for_task_completion(self, task):
        status = task.wait_for_done(sleep_interval=5, callback=self._on_task_update)
        if self.config.DEBUG:
            print(f"Embedding done: {status}")

    def _retrieve_embedding(self, task):
        task = task.retrieve(embedding_option=["visual-text", "audio"])

        if not task.video_embedding or not task.video_embedding.segments:
            raise Exception("Embedding failed")

        return task

    def _process_segments(self, task):
        segments = []
        for segment in task.video_embedding.segments:
            segments.append(
                {
                    "start_time": segment.start_offset_sec,
                    "end_time": segment.end_offset_sec,
                    "scope": segment.embedding_scope,  # "clip" or "video"
                    "modality": segment.embedding_option,  # "text-visual" or "audio"
                    "embedding": segment.embeddings_float,
                }
            )
        return segments

    def extract_video_embedding(
        self,
        filepath: Optional[str] = None,
        url: Optional[str] = None,
        debug=False,
    ):
        segments = self.extract_video_features(filepath, url, debug)

        return [
            segment.embeddings_float
            for segment in segments
            if segment.embedding_scope == "video"
        ]

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
            return res.image_embedding.segments[0].embeddings_float

    def extract_text_embedding(self, input_text: str):
        res = self.client.embed.create(
            model_name="Marengo-retrieval-2.7", text_truncate="start", text=input_text
        )

        if res.text_embedding is not None and res.text_embedding.segments is not None:
            return res.text_embedding.segments[0].embeddings_float
