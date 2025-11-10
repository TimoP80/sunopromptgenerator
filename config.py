import os
from dotenv import load_dotenv

# Build the absolute path to the .env file based on this script's location
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- API Keys ---
SUNO_API_URL = os.getenv("SUNO_API_URL", "https://api.sunoapi.org")

# Files and Uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg'}
MAX_FILE_SIZE = 256 * 1024 * 1024  # 256MB