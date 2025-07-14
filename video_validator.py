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
MAX_FILESIZE = 2000000000



def is_valid_video_file(file_path: str) -> bool:
    if not os.path.exists(file_path):
        return False
    
    if not has_valid_file_extension(file_path):
        return False
    
    probe_data = get_probe_data(file_path)
    if probe_data is None:
        return False
    
    return (
        is_valid_filesize(file_path) and
        has_video_stream(probe_data) and
        is_valid_duration(probe_data) and
        is_valid_dimensions(probe_data)
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
    if file_ext in VALID_VIDEO_EXTENSIONS:
        return True
    else:
      print(f"Invalid file extension. Check if file type supported")
      return False
    

def has_video_stream(probe_data: Dict[str, Any]) -> bool:
    video_streams = [
        stream for stream in probe_data['streams'] 
        if stream['codec_type'] == 'video'
    ]
    
    if not video_streams:
        print(f"No video stream detected. Check if file is corrupted or file type supported")
        return False
    
    legitimate_video_streams = [
        stream for stream in video_streams
        if stream.get('codec_name', '').lower() not in ['mjpeg', 'png', 'bmp', 'gif']
    ]
    
    if len(legitimate_video_streams) > 0:
        return True
    else:
      print(f"No valid video stream detected. Check if file type supported")
      return False
    

def is_valid_duration(probe_data: Dict[str, Any]) -> bool:
    format_info = probe_data.get('format', {})
    duration = format_info.get('duration')
    
    if duration is None:
        return False
    
    try:
        duration_float = float(duration)
        if MIN_DURATION <= duration_float and duration_float <= MAX_DURATION:
            return True
        else:
          print(f"Invalid video duration. Video must duration be between {MIN_DURATION} and {MAX_DURATION} seconds")
          return False
            
    except (ValueError, TypeError):
        return False

def is_valid_dimensions(probe_data: Dict[str, Any]) -> bool:
    stream = probe_data.get('streams', {})[0]
    width = stream.get('width')
    height = stream.get('height')
    print(width)
    print(height)

    if width < MIN_WIDTH or width > MAX_WIDTH:
        print(f"Invalid video width. Video must be between {MIN_WIDTH} and {MAX_WIDTH} pixels wide")
        return False
    if height < MIN_HEIGHT or height > MAX_HEIGHT:
        print(f"Invalid video height. Video must be between {MIN_HEIGHT} and {MAX_HEIGHT} pixels in height")
        return False
    return True

def is_valid_filesize(file_path):
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILESIZE:
        print("file exceeds the maximum size. Ensure files are less than 2GB")
        return False
    return True
