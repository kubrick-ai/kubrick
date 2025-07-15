from twelvelabs import TwelveLabs
from typing import List, Optional
from twelvelabs.models.embed import EmbeddingsTask, SegmentEmbedding


class EmbedService:
    def __init__(self, config):
        self.config = config
        self.api_key = config.TWELVELABS_API_KEY
        self.client = TwelveLabs(api_key=self.api_key)

    def on_task_update(self, task: EmbeddingsTask):
        print(f"  Status={task.status}")

    def print_segments(self, segments: List[SegmentEmbedding], max_elements: int = 5):
        for segment in segments:
            print(
                f"  embedding_scope={segment.embedding_scope} embedding_option={segment.embedding_option} start_offset_sec={segment.start_offset_sec} end_offset_sec={segment.end_offset_sec}"
            )
            if segment.embeddings_float is not None:
                print(f"  embeddings: {segment.embeddings_float[:max_elements]}")

    def extract_video_features(
        self,
        filepath: Optional[str] = None,
        url: Optional[str] = None,
        clip_length: Optional[int] = None,
        start_offset: Optional[float] = None,
        end_offset: Optional[float] = None,
    ):
        clip_length = self.config.DEFAULT_CLIP_LENGTH
        task = self.client.embed.task.create(
            model_name=self.config.EMBEDDING_MODEL_NAME,
            video_file=filepath,
            video_url=url,
            video_clip_length=clip_length,
            video_start_offset_sec=start_offset,
            video_end_offset_sec=end_offset,
            video_embedding_scopes=["clip"],
        )
        if self.config.DEBUG:
            print(
                f"Created task: id={task.id} model_name={task.model_name} status={task.status}"
            )

        status = task.wait_for_done(sleep_interval=5, callback=self.on_task_update)
        if self.config.DEBUG:
            print(f"Embedding done: {status}")

        task = task.retrieve(embedding_option=["visual-text", "audio"])

        if task.video_embedding is None or task.video_embedding.segments is None:
            raise Exception("Embedding failed")

        # TODO: Formalise this return type - right now it is arbitrary (based on Marengo API)
        return task.video_embedding.segments

    def extract_video_embeddings(
        self,
        filepath: Optional[str] = None,
        url: Optional[str] = None,
        debug=False,
    ):
        segments = self.extract_video_features(filepath, url, debug)
        return [segment.embeddings_float for segment in segments]

    def extract_text_embeddings(self, input_text: str):
        res = self.client.embed.create(
            model_name="Marengo-retrieval-2.7", text_truncate="start", text=input_text
        )

        if res.text_embedding is not None and res.text_embedding.segments is not None:
            return res.text_embedding.segments[0].embeddings_float
