from typing import BinaryIO, Optional, List

from app.config import Config
from twelvelabs import TwelveLabs
from twelvelabs.models.embed import EmbeddingsTask


class EmbedService:
    def __init__(self, config=Config()):
        self.config = config
        self.api_key = config.TWELVELABS_API_KEY
        self.client = TwelveLabs(api_key=self.api_key)

    def _on_request_update(self, task: EmbeddingsTask):
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
        embedding_request = self._create_embedding_request(
            filepath, url, clip_length, start_offset, end_offset
        )
        self._wait_for_request_completion(embedding_request)
        segments = self._retrieve_segments(embedding_request)
        return self._normalize_segments(segments)

    def _create_embedding_request(
        self,
        filepath: Optional[str],
        url: Optional[str],
        clip_length: Optional[int],
        start_offset: Optional[float],
        end_offset: Optional[float],
    ):
        clip_length = clip_length or self.config.DEFAULT_CLIP_LENGTH

        embedding_request = self.client.embed.task.create(
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
                f"Created task: id={embedding_request.id} model_name={embedding_request.model_name} status={embedding_request.status}"
            )

        return embedding_request

    def _wait_for_request_completion(self, embedding_request):
        status = embedding_request.wait_for_done(
            sleep_interval=5, callback=self._on_request_update
        )
        if self.config.DEBUG:
            print(f"Embedding done: {status}")

    def _retrieve_segments(self, embedding_request):
        segments = embedding_request.retrieve(embedding_option=["visual-text", "audio"])

        if not segments.video_embedding or not segments.video_embedding.segments:
            raise Exception("Embedding failed")

        return segments.video_embedding.segments

    def _normalize_segments(self, segments):
        result = []
        for segment in segments:
            result.append(
                {
                    "start_time": segment.start_offset_sec,
                    "end_time": segment.end_offset_sec,
                    "scope": segment.embedding_scope,  # "clip" or "video"
                    "modality": segment.embedding_option,  # "text-visual" or "audio"
                    "embedding": segment.embeddings_float,
                }
            )
        return result

    def extract_video_embedding(
        self,
        filepath: Optional[str] = None,
        url: Optional[str] = None,
        query_modality: List[str] = ["visual-text"],
        debug=False,
    ):
        segments = self.extract_video_features(filepath, url, debug)

        return [
            segment["embedding"]
            for segment in segments
            if segment["scope"] == "video" and segment["modality"] in query_modality
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
