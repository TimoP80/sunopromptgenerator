import tkinter as tk
from tkinter import messagebox
import threading
import requests
import time
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
API_KEY = "d3e17d1a490d12ef3b90f29975adfc3d"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
MAX_RETRIES = 5
INITIAL_DELAY = 1     # seconds
BACKOFF_FACTOR = 2    # multiplier

# --- API Logic ---
def get_credits_sync():
    """Fetch remaining credits from Suno AI API with retry/backoff."""
    url = "https://api.sunoapi.org/api/v1/generate/credit"  # documented endpoint
    delay = INITIAL_DELAY

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Attempt {attempt} to fetch credits...")
            response = requests.get(url, headers=HEADERS, timeout=10)
            logger.info(f"HTTP {response.status_code} — {response.text}")

            if response.status_code == 200:
                # Parse JSON and return data
                resp_json = response.json()
                credits = resp_json.get("data")
                if credits is None:
                    logger.error("No 'data' field in response JSON")
                    return {"error": "Malformed response: missing data"}
                logger.info("Credits fetched successfully.")
                return {"credits": credits}
            elif response.status_code == 503:
                logger.warning(f"503 Service Unavailable. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= BACKOFF_FACTOR
            else:
                logger.error(f"Unexpected response: {response.status_code} {response.text}")
                return {"error": f"{response.status_code}: {response.text}"}

        except requests.RequestException as e:
            logger.error(f"Request exception: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= BACKOFF_FACTOR

    logger.error(f"Failed to fetch credits after {MAX_RETRIES} attempts.")
    return {"error": "Failed after retries"}

# --- GUI Logic ---
def fetch_credits():
    """Run get_credits_sync in a separate thread to avoid freezing the GUI."""
    def worker():
        result = get_credits_sync()
        root.after(0, lambda: display_credits(result))
    threading.Thread(target=worker, daemon=True).start()
    status_label.config(text="Loading…")

def display_credits(result):
    """Update GUI with result of credit fetch."""
    status_label.config(text="")  # clear loading text
    if "error" in result:
        messagebox.showerror("Error", result["error"])
    else:
        credits = result.get("credits", "Unknown")
        messagebox.showinfo("Remaining Credits", f"You have {credits} credits remaining.")

# --- Tkinter GUI Setup ---
root = tk.Tk()
root.title("Suno AI Credits Checker")

btn = tk.Button(root, text="Check Remaining Credits", command=fetch_credits)
btn.pack(padx=20, pady=10)

status_label = tk.Label(root, text="", fg="blue")
status_label.pack(pady=5)

root.mainloop()
