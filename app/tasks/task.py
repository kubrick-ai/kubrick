import uuid
import os
import urllib.parse
from datetime import datetime
from typing import List, Optional, TypedDict


class VideoMetadata(TypedDict):
    duration: Optional[int]
    filename: str
    height: Optional[int]
    width: Optional[int]


class Task:
    def __init__(self, video_url: str):
        self.id = str(uuid.uuid4())
        self.status = "processing"
        self.video_url = video_url
        self.clip_ids: List[str] = (
            []
        )  # We don't currently do anything with this attribute
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at: Optional[str] = None
        self.error: Optional[str] = None
        self.metadata: VideoMetadata = {
            "duration": None,
            "filename": self.extract_file_name(video_url),
            "height": None,
            "width": None,
        }

    def mark_ready(self, clip_ids: List[str]):
        self.status = "ready"
        self.clip_ids = clip_ids  # We don't currently do anything with this attribute
        self.updated_at = datetime.utcnow().isoformat()

    def mark_failed(self, error_message: str):
        self.status = "failed"
        self.error = error_message
        self.updated_at = datetime.utcnow().isoformat()

    @staticmethod
    def extract_file_name(s3_url: str) -> str:
        parsed_url = urllib.parse.urlparse(s3_url)
        path = parsed_url.path
        filename = os.path.basename(path)

        name_without_ext, _ = os.path.splitext(filename)
        name_clean = urllib.parse.unquote_plus(name_without_ext)

        return name_clean
