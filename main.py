import os
from dotenv import load_dotenv
import cli

load_dotenv()


DEBUG = os.getenv("DEBUG", "").lower() == "true"

cli.run(DEBUG)

