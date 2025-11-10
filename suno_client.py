import requests
import config
import logging
import time
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError, NonNegativeInt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Custom Exceptions ---
class SunoError(Exception):
    """Base exception for Suno API errors."""
    def __init__(self, message, response_data=None):
        super().__init__(message)
        self.response_data = response_data

class SunoAuthError(SunoError):
    """Raised for authentication errors."""
    pass

class APIParsingError(SunoError):
    """Raised when API response parsing fails."""
    pass

# --- Data Models ---

class SunoClient:
    """A client for interacting with the official Suno API."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.sunoapi.org"):
        if not api_key:
            raise SunoAuthError("API key is required for authentication.")
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}"
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Makes a request to the Suno API with exponential backoff."""
        url = f"{self.base_url}{endpoint}"
        max_retries = 5
        initial_delay = 1.0
        backoff_factor = 2.0

        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, timeout=60, **kwargs)
                
                if response.status_code == 200:
                    if 'application/json' in response.headers.get('Content-Type', ''):
                        return response.json()
                    return response.content
                
                elif response.status_code == 503:
                    delay = initial_delay * (backoff_factor ** attempt)
                    logging.warning(f"Attempt {attempt + 1}: Service unavailable (503). Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                    continue

                response.raise_for_status() # Raise HTTPError for other bad responses (4xx or 5xx)

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    raise SunoAuthError("Unauthorized access. Check your API key.") from e
                if e.response.status_code == 429:
                    raise SunoError("Rate limit exceeded. Please try again later.") from e
                logging.error(f"HTTP Error Response: {e.response.text}")
                raise SunoError(f"HTTP Error: {e.response.status_code} {e.response.reason}") from e
            
            except requests.exceptions.RequestException as e:
                delay = initial_delay * (backoff_factor ** attempt)
                logging.warning(f"Network connection error on attempt {attempt + 1}. Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                continue
        
        raise SunoError(f"Request failed after {max_retries} attempts.")

    def generate_music(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates music using the Suno API v1.
        """
        endpoint = "/api/v1/generate"
        
        is_custom = prompt_data.get('is_custom', False)
        
        payload = {
            "model": "V5",
            "make_instrumental": prompt_data.get('instrumental', False),
        }

        if is_custom:
            payload["title"] = prompt_data.get('title', 'AI Music')
            payload["tags"] = prompt_data.get('tags', '')
            payload["prompt"] = prompt_data.get('prompt', '') # Full lyrics for custom mode
        else:
            payload["prompt"] = prompt_data.get('prompt', '') # Descriptive prompt for simple mode

        logging.info(f"Generating music with payload: {payload}")
        return self._request("POST", endpoint, json=payload)

    def check_generation_status(self, generation_ids: list[str]) -> Dict[str, Any]:
        """
        Checks the status of a music generation request using generation IDs.
        """
        ids_param = ",".join(generation_ids)
        endpoint = f"/api/v1/generate/{ids_param}"
        logging.info(f"Checking generation status for IDs: {ids_param}")
        response_data = self._request("GET", endpoint)

        final_results = {'status': 'processing', 'results': []}

        # Handle cases where the API returns a single error object instead of a list
        if not isinstance(response_data, list):
            if isinstance(response_data, dict) and response_data.get('detail'):
                logging.error(f"Suno API returned an error: {response_data['detail']}")
                final_results['status'] = 'failed'
                final_results['message'] = response_data['detail']
                return final_results
            # If it's not an error, wrap it in a list for consistent processing
            response_data = [response_data]

        statuses = [track.get('status') for track in response_data]

        # 1. Check for failure: if any track has failed, the whole job is failed.
        if any(s in ['error', 'failed', 'stalled'] for s in statuses):
            final_results['status'] = 'failed'
            failed_track = next((t for t in response_data if t.get('status') in ['error', 'failed', 'stalled']), None)
            if failed_track:
                final_results['message'] = failed_track.get('error_message', f"A track entered status: {failed_track.get('status')}")
        
        # 2. Check for completion: if all tracks are complete.
        elif all(s == 'complete' for s in statuses):
            final_results['status'] = 'completed'

        # 3. Otherwise, it's still processing. The status is already 'processing'.

        # Always populate results with any tracks that have completed so far.
        for track in response_data:
            if track.get('status') == 'complete':
                final_results['results'].append({
                    'id': track.get('id'),
                    'audio_url': track.get('audio_url'),
                    'title': track.get('title'),
                    'is_instrumental': track.get('metadata', {}).get('make_instrumental', False),
                })
        
        return final_results

    def get_credits(self) -> Dict[str, Any]:
        """
        Gets the account status and remaining credits for the API key.
        """
        endpoint = "/api/v1/generate/credit"
        logging.info("Fetching account credits...")
        response_data = self._request("GET", endpoint)
        credits = response_data.get("data")
        if credits is None:
            raise APIParsingError("Malformed response from credits endpoint: missing 'data' field.", response_data=response_data)
        return {"credits": credits}

    def download_audio(self, audio_url: str) -> bytes:
        """Downloads audio content from a given URL."""
        logging.info(f"Downloading audio from: {audio_url}")
        try:
            response = requests.get(audio_url, timeout=60)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download audio: {e}")
            raise SunoError(f"Failed to download audio from {audio_url}") from e