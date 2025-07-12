import ffmpeg
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from videoprops import get_video_properties

VALID_VIDEO_EXTENSIONS = [
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', 
    '.m4v', '.3gp', '.ogv', '.mpg', '.mpeg', '.ts', '.mts'
]
MIN_WIDTH = 360
MAX_WIDTH = 3840
MIN_HEIGHT = 360
MAX_HEIGHT = 2160
MIN_DURATION = 4.0
MAX_DURATION = 7200.0



def is_valid_video_file(file_path: str) -> bool:
    if not os.path.exists(file_path):
        return False
    
    if not has_valid_file_extension(file_path):
        return False
    
    probe_data = get_probe_data(file_path)
    if probe_data is None:
        return False
    
    return (
        has_video_stream(probe_data) and
        has_duration(probe_data) and
        is_valid_duration(probe_data)
    )

def get_probe_data(file_path: str) -> Optional[Dict[str, Any]]:
    try:
        return ffmpeg.probe(file_path)
    except ffmpeg.Error:
        return None
    except Exception:
        return None


def has_valid_file_extension(file_path: str) -> bool:
    file_ext = Path(file_path).suffix.lower()
    return file_ext in VALID_VIDEO_EXTENSIONS

def has_video_stream(probe_data: Dict[str, Any]) -> bool:
    video_streams = [
        stream for stream in probe_data['streams'] 
        if stream['codec_type'] == 'video'
    ]
    
    if not video_streams:
        return False
    
    legitimate_video_streams = [
        stream for stream in video_streams
        if stream.get('codec_name', '').lower() not in ['mjpeg', 'png', 'bmp', 'gif']
    ]
    
    return len(legitimate_video_streams) > 0

def has_duration(probe_data: Dict[str, Any]) -> bool:
    format_info = probe_data.get('format', {})
    duration = format_info.get('duration')
    return duration is not None

def is_valid_duration(probe_data: Dict[str, Any]) -> bool:
    format_info = probe_data.get('format', {})
    duration = format_info.get('duration')
    
    if duration is None:
        return False
    
    try:
        duration_float = float(duration)
        return MIN_DURATION <= duration_float <= MAX_DURATION
    except (ValueError, TypeError):
        return False

	

file_path = "content/sailboat.mp4"
props = get_video_properties(file_path)
print(get_aspect_ratio(file))