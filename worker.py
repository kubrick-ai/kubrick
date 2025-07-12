import threading
import tempfile
import os
import requests
from embed import extract_video_features
from vector_db import store
from task_store import task_store

def process_video(task_id: str, video_url: str):
    task = task_store.get_task(task_id)
    if not task:
        return

    try:
        response = requests.get(video_url, stream=True)
        if response.status_code != 200:
            task.mark_failed(f"Failed to download video. HTTP {response.status_code}")
            return

        suffix = os.path.splitext(video_url)[1] or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            temp_path = tmp_file.name

        video_embedding = extract_video_features(temp_path)
        clip_ids = []
        for segment in video_embedding:
            clip_id = store(
                video_url,
                embedding_type=segment.embedding_option,
                start_offset=segment.start_offset_sec,
                end_offset=segment.end_offset_sec,
                embedding=segment.embeddings_float,
            )
            clip_ids.append(clip_id)

        os.remove(temp_path)
        task.mark_ready(clip_ids)

    except Exception as e:
        task.mark_failed(str(e))

def start_background_task(task_id: str, video_url: str):
    thread = threading.Thread(target=process_video, args=(task_id, video_url))
    thread.start()
