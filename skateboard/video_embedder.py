import os
from dotenv import load_dotenv
from twelvelabs import TwelveLabs
from typing import List
from twelvelabs.models.embed import EmbeddingsTask, SegmentEmbedding
import downloader
import vector_db

load_dotenv()
API_KEY = os.getenv('TWELVELABS_API')

vector_db.setup()

downloader.download_youtube("https://www.youtube.com/watch?v=vsESzmEFDWE", "game-highlights")
client = TwelveLabs(api_key=API_KEY)
video_file= "./content/video_data/game-highlights.mp4"

def on_task_update(task: EmbeddingsTask):
    print(f"  Status={task.status}")

def print_segments(segments: List[SegmentEmbedding], max_elements: int = 5):
    for segment in segments:
        print(f"  embedding_scope={segment.embedding_scope} embedding_option={segment.embedding_option} start_offset_sec={segment.start_offset_sec} end_offset_sec={segment.end_offset_sec}")
        print(f"  embeddings: {', '.join(str(segment.embeddings_float[:max_elements]))}")

def store_segments(segments: List[SegmentEmbedding], video_file: str):
    for segment in segments:
        vector_db.store(video_file, segment)

task = client.embed.task.create(model_name="Marengo-retrieval-2.7", video_file=video_file)

print(f"Created task: id={task.id} model_name={task.model_name} status={task.status}")

status = task.wait_for_done(sleep_interval=5,callback=on_task_update)
print(f"Embedding done: {status}")

task = task.retrieve(embedding_option=["visual-text", "audio"])

if task.video_embedding is not None and task.video_embedding.segments is not None:
    store_segments(task.video_embedding.segments, video_file)
