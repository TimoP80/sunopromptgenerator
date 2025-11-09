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
from genre_rules import GENRE_RULES
from suno_client import SunoClient
import pprint

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def read_history():
    """Reads the analysis history from the JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return []

def write_history(data):
    """Writes the analysis history to the JSON file."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        logging.error("Could not write to history file.")

def add_genre_rule_to_file(genre_name, min_bpm, max_bpm):
    """Adds a new genre rule to the GENRE_RULES list in genre_rules.py."""
    genre_rules_path = os.path.join(os.path.dirname(__file__), 'genre_rules.py')

    # Create the new rule dictionary
    new_rule = {
        'genre': genre_name,
        'rules': {
            'tempo': {'min': min_bpm, 'max': max_bpm}
        }
    }

    # Append the new rule to the in-memory list
    GENRE_RULES.append(new_rule)

    # Write the entire updated list back to the file
    with open(genre_rules_path, 'w') as f:
        f.write("GENRE_RULES = ")
        # Use pprint to format the output nicely
        f.write(pprint.pformat(GENRE_RULES))



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

@app.route('/api/add_genre', methods=['POST'])
def add_genre():
    try:
        data = request.get_json()
        logging.info(f"Received request to /api/add_genre with data: {data}")
        genre_name = data.get('genre_name')
        min_bpm = data.get('min_bpm')
        max_bpm = data.get('max_bpm')

        if not all([genre_name, min_bpm, max_bpm]):
            return jsonify({'success': False, 'error': 'Missing genre_name, min_bpm, or max_bpm'}), 400

        min_bpm = int(min_bpm)
        max_bpm = int(max_bpm)

        add_genre_rule_to_file(genre_name, min_bpm, max_bpm)
        return jsonify({
            'success': True,
            'message': f'Genre \'{genre_name}\' added successfully.',
            'genres': GENRE_RULES
        })
    except Exception as e:
        logging.error(f"Error adding genre: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'An internal error occurred.'}), 500

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
        prompt = data.pop('prompt', None)
        is_custom = data.pop('is_custom', False)
        title = data.pop('title', 'AI Music')
        instrumental = data.pop('instrumental', False)

        if not prompt:
            return jsonify({'error': 'Prompt is required.'}), 400

        client = SunoClient()
        # Pass the remaining data from the request to the client
        response = client.generate_music(
            prompt,
            is_custom=is_custom,
            title=title,
            instrumental=instrumental,
            **data
        )
        
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Error generating music: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generation-status/<request_id>', methods=['GET'])
def generation_status(request_id):
    """Checks the status of a music generation request."""
    try:
        client = SunoClient()
        response = client.generation_status(request_id)
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Error checking generation status: {str(e)}")
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

        serve(app, host='0.0.0.0', port=5001)

    start_app()
