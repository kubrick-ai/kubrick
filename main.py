import os
from dotenv import load_dotenv
import cli
from embed import extract_text_features, extract_video_features, print_segments
import vector_db
import downloader

load_dotenv()

# Download a youtube video example
# downloader.download_video("https://www.youtube.com/watch?v=h-pc8KTIV7g&list=RDh-pc8KTIV7g")

DEBUG = os.getenv("DEBUG", "").lower() == "true"

cli.run(DEBUG)