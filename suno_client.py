import requests
import config
import logging
import time
from typing import Optional, Dict, Any, Union

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Custom Exceptions ---
class SunoError(Exception):
    """Base exception for Suno API errors."""
    pass

class SunoAuthError(SunoError):
    """Raised for authentication errors."""
    pass

class SunoRateLimitError(SunoError):
    """Raised for rate limit errors."""
    pass

class SunoServerError(SunoError):
    """Raised for server-side errors."""
    pass

class SunoClient:
    """A client for interacting with the official Suno API."""

    BASE_URL = "https://studio-api.suno.ai"
    STATUS_CODE_MESSAGES = {
        400: "Invalid parameters",
        401: "Unauthorized access",
        404: "Invalid request method or path",
        405: "Rate limit exceeded",
        413: "Theme or prompt too long",
        429: "Insufficient credits",
        430: "Your call frequency is too high. Please try again later.",
        455: "System maintenance",
        500: "Server error",
        503: "Service Unavailable",
    }

    def __init__(self, api_key: Optional[str] = None, retries: int = 3, backoff_factor: float = 0.5):
        self.api_key = api_key or config.SUNO_API_KEY
        if not self.api_key:
            raise SunoAuthError("Suno API key is not configured.")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
        })
        self.retries = retries
        self.backoff_factor = backoff_factor

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Makes a request to the Suno API with error handling and retries.
        """
        url = f"{self.BASE_URL}{endpoint}"
        for attempt in range(self.retries):
            try:
                response = self.session.request(method, url, timeout=60, **kwargs)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                message = self.STATUS_CODE_MESSAGES.get(status_code, 'An unknown API error occurred.')
                
                if status_code == 401:
                    raise SunoAuthError(f"Suno API Error ({status_code}): {message}") from e
                if status_code in [405, 429, 430]:
                    if attempt < self.retries - 1:
                        sleep_time = self.backoff_factor * (2 ** attempt)
                        logging.warning(f"Rate limit exceeded. Retrying in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                        continue
                    raise SunoRateLimitError(f"Suno API Error ({status_code}): {message}") from e
                if status_code >= 500:
                    raise SunoServerError(f"Suno API Error ({status_code}): {message}") from e
                
                raise SunoError(f"Suno API Error ({status_code}): {message}") from e
            except requests.exceptions.RequestException as e:
                raise SunoError(f"Network Connection Error: {e}") from e

    def generate_music(self, prompt: Union[str, Dict[str, str]], is_custom: bool = False, title: str = 'AI Music', instrumental: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Generates music using the Suno API.
        """
        endpoint = "/api/v2/generate"
        
        if is_custom:
            payload = {
                "prompt": prompt.get('lyrics_prompt', ''),
                "tags": prompt.get('style_prompt', ''),
                "title": title,
                "instrumental": instrumental,
                "customMode": True,
                "model": "chirp-v3-0"
            }
        else:
            payload = {
                "prompt": prompt,
                "instrumental": instrumental,
                "customMode": False,
                "model": "chirp-v3-0"
            }
        
        logging.info(f"Generating music with payload: {payload}")
        return self._request("POST", endpoint, json=payload, **kwargs)

    def check_generation_status(self, request_id: str) -> Dict[str, Any]:
        """
        Checks the status of a music generation request.
        """
        endpoint = f"/api/v2/status/{request_id}"
        logging.info(f"Checking generation status for request ID: {request_id}")
        return self._request("GET", endpoint)
    def get_credits(self) -> Dict[str, Any]:
        """
        Gets the remaining credits for the API key.
        """
        endpoint = "/api/v2/credits"
        logging.info("Fetching credits...")
        return self._request("GET", endpoint)

    def get_songs(self, ids: Optional[list[str]] = None) -> Dict[str, Any]:
        """
        Gets a list of all generated songs or specific songs by their IDs.
        """
        endpoint = "/api/v2/songs"
        params = {"ids": ",".join(ids)} if ids else {}
        logging.info(f"Fetching songs with IDs: {ids}" if ids else "Fetching all songs...")
        return self._request("GET", endpoint, params=params)

    def get_song(self, song_id: str) -> Dict[str, Any]:
        """
        Gets detailed information for a single song.
        """
        endpoint = f"/api/v2/songs/{song_id}"
        logging.info(f"Fetching song with ID: {song_id}...")
        return self._request("GET", endpoint)

    def generate_lyrics(self, prompt: str) -> Dict[str, Any]:
        """
        Generates lyrics using the Suno API.
        """
        endpoint = "/api/v2/lyrics"
        payload = {"prompt": prompt}
        logging.info(f"Generating lyrics with prompt: {prompt}")
        return self._request("POST", endpoint, json=payload)

    def extend_audio(self, audio_path: str, start_time: float) -> Dict[str, Any]:
        """
        Uploads and extends an existing audio file.
        """
        endpoint = "/api/v2/extend"
        with open(audio_path, "rb") as f:
            files = {"file": (audio_path, f, "audio/mpeg")}
            data = {"start_time": start_time}
            logging.info(f"Extending audio file: {audio_path} from {start_time}s")
            return self._request("POST", endpoint, files=files, data=data)