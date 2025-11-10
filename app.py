from flask import Flask, request, jsonify, Response, stream_with_context, render_template, url_for
import json
from werkzeug.utils import secure_filename
import os
import sys
import traceback
import torch
import cpuinfo
import logging
import multiprocessing
from audio_analyzer import AudioAnalyzer
from prompt_generator import PromptGenerator
from suno_client import SunoClient
import pprint

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Globals ---
GENRE_RULES = []

def load_genre_rules():
    """Loads genre rules from the JSON file."""
    global GENRE_RULES
    try:
        with open('genre_rules.json', 'r') as f:
            GENRE_RULES = json.load(f)
        logging.info(f"Successfully loaded {len(GENRE_RULES)} genre rules.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Could not load or parse genre_rules.json: {e}")
        GENRE_RULES = []

# --- Hardware Detection & Model Cache ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_CACHE = {}
logging.info(f"Application starting. AI processing device set to: {DEVICE.upper()}")

import config

app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'analysis_history.json')
GENERATION_HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'generation_history.json')

def read_history(file_path=HISTORY_FILE):
    """Reads a history file from the given path."""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return []

def write_history(data, file_path=HISTORY_FILE):
    """Writes data to a history file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        logging.error(f"Could not write to history file: {file_path}")

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), 'suno_accounts.json')

def load_accounts():
    """Loads Suno accounts from the JSON file."""
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    try:
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return {}

def save_accounts(data):
    """Saves Suno accounts to the JSON file."""
    try:
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        logging.error("Could not write to accounts file.")

def get_suno_client_from_request():
    """Helper to get Suno client from request headers."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise ValueError("Authorization header with Bearer token is required.")
    api_key = auth_header.split(' ')[1]
    return SunoClient(api_key=api_key, base_url=config.SUNO_API_URL)

@app.route('/')
def index():
    """Serve the main page"""
    # Detect CPU and GPU hardware
    cpu_model = cpuinfo.get_cpu_info().get('brand_raw', 'N/A')
    
    # Check for PyTorch (Whisper & Demucs) GPU support
    pytorch_gpu = torch.cuda.is_available()
    
    gpu_model = "N/A"
    if pytorch_gpu:
        gpu_model = torch.cuda.get_device_name(0)

    return render_template('index.html', cpu_model=cpu_model, gpu_model=gpu_model, pytorch_gpu=pytorch_gpu)

@app.route('/api/analyze', methods=['POST'])
def analyze_audio():
    """Analyze uploaded audio file and generate prompt"""
    def generate_progress():
        try:
            logging.info("Received request to /api/analyze")
            # Check if file is present
            if 'audio' not in request.files:
                yield f"data: {json.dumps({'error': 'No audio file provided'})}\n\n"
                return
            
            file = request.files['audio']
            logging.info(f"Received file: {file.filename}")
            
            if file.filename == '' or not allowed_file(file.filename):
                yield f"data: {json.dumps({'error': 'Invalid file'})}\n\n"
                return
            
            # Save file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logging.info(f"File saved to: {filepath}")
            
            try:
                yield f"data: {json.dumps({'status': 'Analyzing audio features...', 'progress': 10})}\n\n"
                analyzer = AudioAnalyzer(filepath, device=DEVICE, model_cache=MODEL_CACHE)
                features = analyzer.analyze()
                
                yield f"data: {json.dumps({'status': 'Detecting tempo and key...', 'progress': 25})}\n\n"
                selected_genre = request.form.get('selected_genre', None)
                
                yield f"data: {json.dumps({'status': 'Classifying genre and mood...', 'progress': 30})}\n\n"
                genre = analyzer.classify_genre(selected_genre=selected_genre)
                mood = analyzer.classify_mood()
                
                yield f"data: {json.dumps({'status': 'Analyzing instruments...', 'progress': 35})}\n\n"
                instruments = analyzer.detect_instruments(genre)
                has_vocals = analyzer.detect_vocals()
                
                lyrics, vocal_gender = None, None
                if has_vocals:
                    yield f"data: {json.dumps({'status': 'Separating vocals (can be slow)...', 'progress': 40})}\n\n"
                    model_quality = request.form.get('model_quality', 'base')
                    demucs_model = request.form.get('demucs_model', 'htdemucs_ft')
                    save_vocals = request.form.get('save_vocals') == 'true'
                    
                    yield f"data: {json.dumps({'status': f'Transcribing lyrics with Whisper ({model_quality})...', 'progress': 60})}\n\n"
                    vocal_info = analyzer.extract_lyrics(
                        model_quality=model_quality,
                        demucs_model=demucs_model,
                        save_vocals=save_vocals,
                        output_dir=app.config['UPLOAD_FOLDER']
                    )
                    lyrics = vocal_info.get('lyrics')
                    vocal_gender = vocal_info.get('gender')
                
                yield f"data: {json.dumps({'status': 'Generating prompts...', 'progress': 90})}\n\n"
                generator = PromptGenerator(features, genre, mood, instruments, has_vocals, lyrics, vocal_gender)
                variations = generator.generate_variations()
                
                # Prepare final response
                response = {
                    'success': True,
                    'analysis': {
                        'genre': genre,
                        'mood': mood,
                        'instruments': instruments,
                        'has_vocals': has_vocals,
                        'lyrics': lyrics,
                        'vocal_gender': vocal_gender,
                        'tempo': features.get('tempo'),
                        'key': features.get('key'),
                        'energy': features.get('energy'),
                        'full_analysis_data': features
                    },
                    'prompts': variations
                }
                # Store the final result in a session or a temporary cache
                # For simplicity, we'll just pass it back to the client to be exported
                yield f"data: {json.dumps({'status': 'Complete!', 'progress': 100, 'result': response})}\n\n"
                
            finally:
                # In the new flow, we might not want to clean up immediately
                # The client will tell us when it's okay to delete the file
                if DEVICE == 'cuda':
                    torch.cuda.empty_cache()
        
        except Exception as e:
            logging.error(f"Error analyzing audio: {str(e)}")
            logging.error(traceback.format_exc())
            yield f"data: {json.dumps({'error': f'Error analyzing audio: {str(e)}'})}\n\n"
            return

    return Response(stream_with_context(generate_progress()), content_type='text/event-stream')

@app.route('/api/preprocess', methods=['POST'])
def preprocess_audio():
    """Extracts basic metadata from the audio file without full analysis."""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file'}), 400
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        analyzer = AudioAnalyzer(filepath, device=DEVICE, model_cache=MODEL_CACHE)
        metadata = analyzer.extract_metadata()
        
        # --- Also perform a quick analysis for more detailed info ---
        try:
            # Load audio if not already loaded (some metadata doesn't require it)
            if analyzer.y is None:
                analyzer.load_audio()
            
            quick_analysis = {
                "Tempo (BPM)": analyzer.get_tempo(),
                "Key": analyzer.get_key(),
                "Energy": analyzer.get_energy().title()
            }
            # Combine metadata and quick analysis, giving preference to specific analysis keys
            metadata.update(quick_analysis)
        except Exception as e:
            logging.warning(f"Could not perform quick analysis: {e}")

        return jsonify({'success': True, 'metadata': metadata, 'filepath': filepath})
        
    except Exception as e:
        logging.error(f"Error during preprocessing: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


@app.route('/api/genres', methods=['GET'])
def get_genres():
    """Return the current list of genre rules."""
    return jsonify(GENRE_RULES)

@app.route('/api/export', methods=['POST'])
def export_results():
    """Exports analysis results to a JSON file."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Set headers to trigger file download
        headers = {
            'Content-Disposition': 'attachment; filename=analysis.json',
            'Content-Type': 'application/json'
        }
        return Response(json.dumps(data, indent=4), headers=headers)
        
    except Exception as e:
        logging.error(f"Error exporting results: {str(e)}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/generate-music', methods=['POST'])
def generate_music():
    """Triggers music generation using the Suno API."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid payload.'}), 400

        # Prepare the payload for the Suno client
        prompt_data = {
            'prompt': data.get('prompt'),
            'is_custom': data.get('is_custom', False),
            'instrumental': data.get('instrumental', False),
            'title': data.get('title'),
            'tags': data.get('tags')
        }

        # Handle the structure of the 'prompt' field for custom generations
        if prompt_data['is_custom'] and isinstance(data.get('prompt'), dict):
            prompt_dict = data.get('prompt', {})
            prompt_data['prompt'] = prompt_dict.get('lyrics_prompt', '')
            # If tags are not provided directly, use style_prompt
            if not prompt_data['tags']:
                prompt_data['tags'] = prompt_dict.get('style_prompt', '')

        client = get_suno_client_from_request()
        response = client.generate_music(prompt_data)
        
        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logging.error(f"Error generating music: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generation-status/<request_id>', methods=['GET'])
def generation_status(request_id):
    """Checks the status of a music generation request."""
    try:
        client = get_suno_client_from_request()
        response = client.check_generation_status(request_id.split(','))

        # If the generation is complete, save it to history
        if response.get('status') == 'completed':
            try:
                history = read_history(GENERATION_HISTORY_FILE)
                # Prevent duplicates by checking existing IDs
                existing_ids = {item['id'] for item in history}
                
                for track in response.get('results', []):
                    if track['id'] not in existing_ids:
                        import datetime
                        import uuid
                        track['generation_id'] = str(uuid.uuid4())
                        track['timestamp'] = datetime.datetime.now().isoformat()
                        history.insert(0, track)

                write_history(history, GENERATION_HISTORY_FILE)
            except Exception as e:
                logging.error(f"Could not save generation to history: {e}")

        return jsonify(response)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logging.error(f"Error checking generation status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/credits', methods=['GET'])
def get_credits():
    """Gets the remaining credits for the Suno API key."""
    try:
        client = get_suno_client_from_request()
        credits_info = client.get_credits()
        return jsonify(credits_info)
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logging.error(f"Error fetching credits: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Returns the analysis history."""
    history = read_history()
    return jsonify(history)

@app.route('/api/history', methods=['POST'])
def save_to_history():
    """Saves an analysis result to the history."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        history = read_history()
        # Add a timestamp and a unique ID
        import datetime
        import uuid
        data['id'] = str(uuid.uuid4())
        data['timestamp'] = datetime.datetime.now().isoformat()
        
        history.insert(0, data) # Add to the beginning of the list
        write_history(history)
        
        return jsonify({'success': True, 'message': 'Analysis saved to history.'})
        
    except Exception as e:
        logging.error(f"Error saving to history: {str(e)}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/generation-history', methods=['GET'])
def get_generation_history():
    """Returns the music generation history."""
    history = read_history(GENERATION_HISTORY_FILE)
    return jsonify(history)

@app.route('/api/generation-history', methods=['POST'])
def save_generation_to_history():
    """Saves a music generation result to the history."""
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'error': 'Invalid data provided.'}), 400
        
        history = read_history(GENERATION_HISTORY_FILE)
        
        # Avoid duplicates
        if any(item['id'] == data['id'] for item in history):
            return jsonify({'success': False, 'message': 'Item already in history.'})

        import datetime
        import uuid
        data['generation_id'] = str(uuid.uuid4())
        data['timestamp'] = datetime.datetime.now().isoformat()
        
        history.insert(0, data)
        write_history(history, GENERATION_HISTORY_FILE)
        
        return jsonify({'success': True, 'message': 'Generation saved to history.'})
        
    except Exception as e:
        logging.error(f"Error saving generation to history: {str(e)}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Returns the list of saved Suno accounts."""
    accounts = load_accounts()
    # For security, don't return the API keys, just the names and default status
    account_info = {
        name: {"default": data.get("default", False)}
        for name, data in accounts.items()
    }
    return jsonify(account_info)

@app.route('/api/accounts', methods=['POST'])
def add_account():
    """Adds a new Suno account."""
    try:
        data = request.get_json()
        name = data.get('name')
        api_key = data.get('api_key')

        if not name or not api_key:
            return jsonify({'error': 'Account name and API key are required.'}), 400

        accounts = load_accounts()
        if name in accounts:
            return jsonify({'error': 'An account with this name already exists.'}), 409

        accounts[name] = {"api_key": api_key}
        
        # If this is the first account, make it the default
        if len(accounts) == 1:
            accounts[name]['default'] = True
            
        save_accounts(accounts)
        return jsonify({'success': True, 'message': f"Account '{name}' added."})

    except Exception as e:
        logging.error(f"Error adding account: {str(e)}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/accounts', methods=['DELETE'])
def remove_account():
    """Removes a Suno account."""
    try:
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Account name is required.'}), 400

        accounts = load_accounts()
        if name not in accounts:
            return jsonify({'error': 'Account not found.'}), 404

        was_default = accounts[name].get('default', False)
        del accounts[name]

        # If the deleted account was the default, and there are other accounts,
        # make the first remaining account the new default.
        if was_default and accounts:
            first_account_name = next(iter(accounts))
            accounts[first_account_name]['default'] = True

        save_accounts(accounts)
        return jsonify({'success': True, 'message': f"Account '{name}' removed."})

    except Exception as e:
        logging.error(f"Error removing account: {str(e)}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/accounts/default', methods=['POST'])
def set_default_account():
    """Sets a specific Suno account as the default."""
    try:
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Account name is required.'}), 400

        accounts = load_accounts()
        if name not in accounts:
            return jsonify({'error': 'Account not found.'}), 404

        for acc_name, acc_data in accounts.items():
            acc_data['default'] = (acc_name == name)
            
        save_accounts(accounts)
        return jsonify({'success': True, 'message': f"Account '{name}' set as default."})

    except Exception as e:
        logging.error(f"Error setting default account: {str(e)}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/download-audio', methods=['GET'])
def download_audio():
    """Downloads the audio from a given URL."""
    audio_url = request.args.get('url')
    title = request.args.get('title', 'suno_generation')

    if not audio_url:
        return jsonify({'error': 'Audio URL is required.'}), 400

    try:
        # We need a client to download, but the key isn't strictly needed for a public URL.
        # However, it's good practice to use the client's session.
        client = get_suno_client_from_request()
        audio_data = client.download_audio(audio_url)
        
        return Response(
            audio_data,
            mimetype='audio/mpeg',
            headers={'Content-Disposition': f'attachment;filename={secure_filename(title)}.mp3'}
        )
    except ValueError as e: # Handles auth errors from get_suno_client_from_request
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logging.error(f"Error downloading audio: {str(e)}")
        return jsonify({'error': 'Failed to download audio.'}), 500


if __name__ == '__main__':
    multiprocessing.freeze_support()

    def start_app():
        """Starts the Flask application using Waitress."""
        # Check if running in a PyInstaller bundle
        is_bundle = hasattr(sys, '_MEIPASS')

        if is_bundle:
            try:
                import pyi_splash
                pyi_splash.update_text("Initializing application...")
            except (ImportError, RuntimeError):
                pass  # Ignore if splash screen fails
        else:
            logging.info("Initializing application...")

        from waitress import serve
        
        if is_bundle:
            try:
                import pyi_splash
                pyi_splash.update_text("Starting web server...")
            except (ImportError, RuntimeError):
                pass
        else:
            logging.info("Starting web server...")

        print("Starting Suno v5 Prompt Generator...")
        print("Open your browser to http://localhost:5001")
        
        # Close the splash screen once the server is ready
        if is_bundle:
            try:
                import pyi_splash
                pyi_splash.close()
            except (ImportError, RuntimeError):
                pass # Not running in a PyInstaller bundle
        
        load_genre_rules()
        serve(app, host='0.0.0.0', port=5001)

    start_app()
