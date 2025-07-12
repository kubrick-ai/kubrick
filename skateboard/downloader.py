import os
from pytubefix import YouTube
from pytubefix.cli import on_progress

def download_youtube(video_url, name):
	output_vid = f"./content/video_data/{name}.mp4"
	output_dir = os.path.dirname(output_vid)

	# Create output directory if it doesn't exist
	os.makedirs(output_dir, exist_ok=True)

	print(f"Downloading video from {video_url} to {output_vid}...")

	yt = YouTube(video_url, on_progress_callback=on_progress)
	stream = yt.streams.get_highest_resolution()

	if stream:
		stream.download(output_path=output_dir, filename=os.path.basename(output_vid))
		print(f"\nVideo downloaded successfully to {output_vid}")
	else:
		print("Error: Could not find a suitable video stream.")

