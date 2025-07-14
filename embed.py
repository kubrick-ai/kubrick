import os
from twelvelabs import TwelveLabs
from typing import List, Optional, Literal
from twelvelabs.models.embed import EmbeddingsTask, SegmentEmbedding
from dotenv import load_dotenv

load_dotenv()


TWELVELABS_API_KEY = os.getenv("TWELVELABS_API_KEY", "")


def on_task_update(task: EmbeddingsTask):
    print(f"  Status={task.status}")


def print_segments(segments: List[SegmentEmbedding], max_elements: int = 5):
    for segment in segments:
        print(
            f"  embedding_scope={segment.embedding_scope} embedding_option={segment.embedding_option} start_offset_sec={segment.start_offset_sec} end_offset_sec={segment.end_offset_sec}"
        )
        if segment.embeddings_float is not None:
            print(f"  embeddings: {segment.embeddings_float[:max_elements]}")


def extract_video_features(
    filepath: Optional[str] = None,
    url: Optional[str] = None,
    DEBUG=False,
):
    # 1. Initialize the client
    client = TwelveLabs(api_key=TWELVELABS_API_KEY)

    # 2. Upload a video
    task = client.embed.task.create(
        model_name="Marengo-retrieval-2.7",
        video_file=filepath,
        video_url=url,
        # video_clip_length=5,
        # video_start_offset_sec=30,
        # video_end_offset_sec=60,
        video_embedding_scopes=["clip"],
    )
    if DEBUG:
        print(
            f"Created task: id={task.id} model_name={task.model_name} status={task.status}"
        )

    # 3. Monitor the status

    status = task.wait_for_done(sleep_interval=5, callback=on_task_update)
    if DEBUG:
        print(f"Embedding done: {status}")

    # 4. Retrieve the embeddings
    task = task.retrieve(embedding_option=["visual-text", "audio"])

    # 5. Process the results
    if task.video_embedding is None or task.video_embedding.segments is None:
        raise Exception("Embedding failed")

    return task.video_embedding.segments


def extract_video_embeddings(
    filepath: Optional[str] = None,
    url: Optional[str] = None,
    DEBUG=False,
):
    segments = extract_video_features(filepath, url, DEBUG)
    return [segment.embeddings_float for segment in segments]


def extract_text_features(input: str):
    client = TwelveLabs(api_key=TWELVELABS_API_KEY)

    res = client.embed.create(
        model_name="Marengo-retrieval-2.7", text_truncate="start", text=input
    )

    if res.text_embedding is not None and res.text_embedding.segments is not None:
        return res.text_embedding.segments[0].embeddings_float
