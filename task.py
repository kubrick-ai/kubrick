import uuid
from datetime import datetime
from typing import List, Optional

class Task:
    def __init__(self, video_url: str):
        # self.id = f"{video_url.split('/')[-1]}_{uuid.uuid4()}" # Originally I had it to this, but seems unneccessary could prob delete.
        self.id = str(uuid.uuid4())
        self.status = "processing"
        self.video_url = video_url
        self.clip_ids: List[str] = []                   # We don't currently do anything with this attribute
        self.created_at = datetime.utcnow().isoformat()
        self.completed_at: Optional[str] = None
        self.error: Optional[str] = None

    def mark_ready(self, clip_ids: List[str]):
        self.status = "ready"
        self.clip_ids = clip_ids                        # We don't currently do anything with this attribute
        self.completed_at = datetime.utcnow().isoformat()

    def mark_failed(self, error_message: str):
        self.status = "failed"
        self.error = error_message
        self.completed_at = datetime.utcnow().isoformat()
