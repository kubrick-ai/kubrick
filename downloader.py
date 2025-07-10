import yt_dlp
import os

def download_video(url, output_path="./downloads"):
    os.makedirs(output_path, exist_ok=True)

    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title).100s.%(ext)s'),
        'format': 'mp4',
        # If we use 'bestvideo+bestaudio/best' it requires ffmpeg
        # 'format': 'bestvideo+bestaudio/best',
        'quiet': False,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        file_path = ydl.prepare_filename(info)
        if os.path.exists(file_path):
            print(f"Video already exists {file_path}")
            print("Skipping download.")
            return None

        print("\nVideo Info Preview:")
        print(f"Title     : {info.get('title')}")
        # Just keeping it here in case we want uploader information (probably not)
        # print(f"Uploader  : {info.get('uploader')}")
        print(f"Duration  : {int(info.get('duration', 0))} seconds")
        print(f"Resolution: {info.get('width')}x{info.get('height')}")

        proceed = input("Is this the video you want to download? (y/n): ").strip().lower()
        if proceed not in ['y', 'yes']:
            print("Download cancelled.")
            return None

        result = ydl.download([url])
        return result