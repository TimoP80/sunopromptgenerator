from flask import Flask, request, jsonify, Response, stream_with_context, render_template, url_for
import json
from werkzeug.utils import secure_filename
import os
import traceback
import torch
import cpuinfo
import logging
from audio_analyzer import AudioAnalyzer
from prompt_generator import PromptGenerator
from genre_rules import GENRE_RULES
import pprint

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import config

app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

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
        pprint.pprint(GENRE_RULES, f)



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
                analyzer = AudioAnalyzer(filepath)
                features = analyzer.analyze()
                
                yield f"data: {json.dumps({'status': 'Classifying genre and mood...', 'progress': 25})}\n\n"
                selected_genre = request.form.get('selected_genre', None)
                genre = analyzer.classify_genre(selected_genre=selected_genre)
                mood = analyzer.classify_mood()
                instruments = analyzer.detect_instruments()
                has_vocals = analyzer.detect_vocals()
                
                lyrics, vocal_gender = None, None
                if has_vocals:
                    yield f"data: {json.dumps({'status': 'Separating vocals (this can be slow)...', 'progress': 40})}\n\n"
                    model_quality = request.form.get('model_quality', 'base')
                    vocal_info = analyzer.extract_lyrics(model_quality=model_quality)
                    lyrics = vocal_info.get('lyrics')
                    vocal_gender = vocal_info.get('gender')
                
                yield f"data: {json.dumps({'status': 'Generating prompts...', 'progress': 90})}\n\n"
                generator = PromptGenerator(features, genre, mood, instruments, has_vocals, lyrics, vocal_gender)
                variations = generator.generate_variations()
                
                # Prepare final response
                response = {
                    'success': True,
                    'analysis': {
                        'tempo': features['tempo'],
                        'key': features['key'],
                        'energy': features['energy'],
                        'genre': genre,
                        'mood': mood,
                        'instruments': instruments,
                        'has_vocals': has_vocals,
                        'lyrics': lyrics,
                        'vocal_gender': vocal_gender
                    },
                    'prompts': variations
                }
                yield f"data: {json.dumps({'status': 'Complete!', 'progress': 100, 'result': response})}\n\n"
                
            finally:
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
        
        except Exception as e:
            logging.error(f"Error analyzing audio: {str(e)}")
            logging.error(traceback.format_exc())
            yield f"data: {json.dumps({'error': f'Error analyzing audio: {str(e)}'})}\n\n"

    return Response(stream_with_context(generate_progress()), content_type='text/event-stream')

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

def start_app():
    """Starts the Flask application using Waitress."""
    from waitress import serve
    print("Starting Suno v5 Prompt Generator...")
    print("Open your browser to http://localhost:5000")
    serve(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    start_app()
