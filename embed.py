import os
from twelvelabs import TwelveLabs
from typing import List
from twelvelabs.models.embed import EmbeddingsTask, SegmentEmbedding
from dotenv import load_dotenv

load_dotenv()


TWELVELABS_API_KEY = os.getenv("TWELVELABS_API_KEY")


def on_task_update(task: EmbeddingsTask):
    print(f"  Status={task.status}")


def print_segments(segments: List[SegmentEmbedding], max_elements: int = 5):
    for segment in segments:
        print(
            f"  embedding_scope={segment.embedding_scope} embedding_option={segment.embedding_option} start_offset_sec={segment.start_offset_sec} end_offset_sec={segment.end_offset_sec}"
        )
        print(f"  embeddings: {segment.embeddings_float[:max_elements]}")


def extract_video_features(video_filepath: str):
    # 1. Initialize the client
    client = TwelveLabs(api_key=TWELVELABS_API_KEY)

    # 2. Upload a video
    task = client.embed.task.create(
        model_name="Marengo-retrieval-2.7",
        video_file=video_filepath,
        # video_clip_length=5,
        # video_start_offset_sec=30,
        # video_end_offset_sec=60,
        video_embedding_scopes=["clip"],
    )
    print(
        f"Created task: id={task.id} model_name={task.model_name} status={task.status}"
    )

    # 3. Monitor the status

    status = task.wait_for_done(sleep_interval=5, callback=on_task_update)
    print(f"Embedding done: {status}")

    # 4. Retrieve the embeddings
    task = task.retrieve(embedding_option=["visual-text", "audio"])

    # 5. Process the results
    if task.video_embedding is None or task.video_embedding.segments is None:
        raise Exception("Embedding failed")

    print_segments(task.video_embedding.segments)
    return task.video_embedding.segments


def extract_text_features(input: str):
    client = TwelveLabs(api_key=TWELVELABS_API_KEY)

    res = client.embed.create(
        model_name="Marengo-retrieval-2.7", text_truncate="start", text=input
    )

    if res.text_embedding is not None and res.text_embedding.segments is not None:
        return res.text_embedding.segments[0].embeddings_float
