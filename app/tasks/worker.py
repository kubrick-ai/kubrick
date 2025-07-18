import threading
import tempfile
import os
import requests
import json
import subprocess
import shutil
from app.services.embed_service import EmbedService
from app.services.vector_db_service import VectorDBService
from .task_store import task_store
from typing import Tuple


def process_video(
    task_id: str,
    video_url: str,
    embed_service: EmbedService,
    vector_db_service: VectorDBService,
):
    task = task_store.get_task(task_id)
    if not task:
        return

    try:
        temp_path = download_to_temp_file(video_url)
        video_segments = embed_service.extract_video_features(filepath=temp_path)

        clip_ids = get_clip_ids(video_segments)
        width, height, duration = get_video_metadata(temp_path)

        update_task_metadata(task, width, height, duration)

        # Store video + embeddings
        video_metadata = {
            "url": video_url,
            "filename": task.metadata["filename"],
            "duration": duration,
            "height": height,
            "width": width,
        }
        vector_db_service.store(video_metadata, video_segments)

        os.remove(temp_path)
        task.mark_ready(clip_ids)

    except Exception as e:
        task.mark_failed(str(e))


def download_to_temp_file(video_url: str) -> str:
    response = requests.get(video_url, stream=True)
    if response.status_code != 200:
        raise Exception(f"Failed to download video. HTTP {response.status_code}")

    suffix = os.path.splitext(video_url)[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        for chunk in response.iter_content(chunk_size=8192):
            tmp_file.write(chunk)
        return tmp_file.name


def get_clip_ids(segments: list[dict]) -> list[str]:
    return [f"{s['start_time']}-{s['end_time']}" for s in segments]


def update_task_metadata(task, width: int, height: int, duration: float):
    task.metadata["width"] = width
    task.metadata["height"] = height
    task.metadata["duration"] = duration


def start_background_task(
    task_id: str,
    video_url: str,
    embed_service: EmbedService = None,
    vector_db_service: VectorDBService = None,
):
    # Create service instances if not provided
    if embed_service is None:
        from app.config import Config

        embed_service = EmbedService(Config())
    if vector_db_service is None:
        from app.config import Config

        vector_db_service = VectorDBService(Config())

    thread = threading.Thread(
        target=process_video,
        args=(task_id, video_url, embed_service, vector_db_service),
    )
    thread.start()


def ensure_ffprobe_available():
    if shutil.which("ffprobe") is None:
        raise EnvironmentError("ffprobe not found in system PATH")


def run_ffprobe(path: str, timeout: int = 10) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File does not exist: {path}")

    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe error: {result.stderr.strip()}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON returned from ffprobe")


def extract_resolution(probe: dict) -> tuple[int, int]:
    video_streams = [
        s for s in probe.get("streams", []) if s.get("codec_type") == "video"
    ]
    if not video_streams:
        raise ValueError("No video stream found")

    stream = video_streams[0]
    width = int(stream.get("width", 0))
    height = int(stream.get("height", 0))

    if not width or not height:
        raise ValueError("Missing width or height in stream")

    return width, height


def extract_duration(probe: dict) -> float:
    duration_str = probe.get("format", {}).get("duration")
    if not duration_str:
        raise ValueError("Duration not found")

    return float(duration_str)


def get_video_metadata(path: str, timeout: int = 10) -> tuple[int, int, float]:
    ensure_ffprobe_available()
    probe = run_ffprobe(path, timeout)
    width, height = extract_resolution(probe)
    duration = extract_duration(probe)

    return width, height, duration
