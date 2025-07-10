import yt_dlp
import os
from typing import Optional, Dict

def prepare_output_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def show_video_info(info: dict) -> None:
    print("\nVideo Info Preview:")
    print(f"Title     : {info.get('title')}")
    # Just keeping it here in case we want uploader information (probably not)
    # print(f"Uploader  : {info.get('uploader')}")
    print(f"Duration  : {int(info.get('duration', 0))} seconds")
    print(f"Resolution: {info.get('width')}x{info.get('height')}")

def confirm_download() -> bool:
    proceed = input("Is this the video you want to download? (y/n): ").strip().lower()
    return proceed in ['y', 'yes']

def download_video(url: str, output_path: str ="./downloads") -> Optional[int]:
    prepare_output_folder(output_path)

    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title).100s.%(ext)s'),
        'format': 'mp4',
        # If we use 'bestvideo+bestaudio/best' it requires ffmpeg
        # 'format': 'bestvideo+bestaudio/best',
        'quiet': False,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            file_path = ydl.prepare_filename(info)

            if os.path.exists(file_path):
                print(f"Video already exists {file_path}")
                print("Skipping download.")
                return None

            show_video_info(info)

            if not confirm_download():
                print("Download cancelled.")
                return None

            result = ydl.download([url])
            return result
    
    except yt_dlp.utils.DownloadError as e:
        print(f"Download failed: {e}")
        return None
    
    except Exception as e:
        print(f"An unexpected error occured: {e}")
        return None