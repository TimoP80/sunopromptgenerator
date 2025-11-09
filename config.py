import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
SUNO_API_KEY = os.getenv("SUNO_API_KEY")

# Files and Uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg'}
MAX_FILE_SIZE = 256 * 1024 * 1024  # 256MB