import librosa
import numpy as np
import soundfile as sf
import whisper
import os
import torch
import subprocess
import importlib
import genre_rules
# Demucs v4 changed its API. We create a wrapper class to mimick the old Separator class.
from demucs.apply import apply_model, BagOfModels
from demucs.pretrained import get_model
from demucs.audio import AudioFile, save_audio, convert_audio
import torchaudio

def load_track(track, audio_channels, samplerate):
    errors = {}
    wav = None

    try:
        wav = AudioFile(track).read(
            streams=0,
            samplerate=samplerate,
            channels=audio_channels)
    except FileNotFoundError:
        errors['ffmpeg'] = 'FFmpeg is not installed.'
    except subprocess.CalledProcessError:
        errors['ffmpeg'] = 'FFmpeg could not read the file.'

    if wav is None:
        try:
            wav, sr = torchaudio.load(str(track))
        except RuntimeError as err:
            errors['torchaudio'] = err.args[0]
        else:
            wav = convert_audio(wav, sr, samplerate, audio_channels)

    if wav is None:
        raise RuntimeError(f"Could not load file {track}. "
                           f"Maybe it is not a supported file format? Errors: {errors}")
    return wav
class Separator:
    def __init__(self, model_name='htdemucs_ft', device='cpu'):
        self.model = get_model(name=model_name)
        if self.model is None:
            raise ValueError(f"Could not find model {model_name}")
        self.model.to(device)
        self.model.eval()
        self.device = device
        self.samplerate = self.model.samplerate
        self.audio_channels = self.model.audio_channels

    def separate_audio_file(self, file_path):
        wav = load_track(file_path, self.audio_channels, self.samplerate)
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()
        wav = wav.to(self.device)
        
        sources = apply_model(self.model, wav[None], device=self.device, split=True, overlap=0.25, progress=True)[0]
        sources = sources * ref.std() + ref.mean()
        
        separated_tracks = {}
        for i, source_name in enumerate(self.model.sources):
            separated_tracks[source_name] = sources[i].cpu().numpy()
            
        return None, separated_tracks

class AudioAnalyzer:
    """Analyzes audio files to extract musical features"""
    
    def __init__(self, audio_path):
        self.audio_path = audio_path
        self.y = None
        self.sr = None
        self.features = {}
        
    def load_audio(self):
        """Load audio file"""
        self.y, self.sr = librosa.load(self.audio_path, sr=22050, duration=60)
        
    def analyze(self):
        """Perform complete audio analysis"""
        self.load_audio()
        
        # Extract all features
        self.features['tempo'] = self.get_tempo()
        self.features['key'] = self.get_key()
        self.features['energy'] = self.get_energy()
        self.features['spectral_centroid'] = self.get_spectral_centroid()
        self.features['zero_crossing_rate'] = self.get_zero_crossing_rate()
        self.features['mfcc'] = self.get_mfcc()
        self.features['chroma'] = self.get_chroma()
        self.features['spectral_rolloff'] = self.get_spectral_rolloff()
        
        return self.features
    
    def get_tempo(self):
        """Extract tempo (BPM)"""
        # Use beat tracking which can be more robust for electronic music
        # by providing a tighter start_bpm to guide the algorithm.
        _, beat_frames = librosa.beat.beat_track(y=self.y, sr=self.sr, start_bpm=120, units='frames')
        beat_times = librosa.frames_to_time(beat_frames, sr=self.sr)
        
        # If we have enough beats, calculate tempo from the median interval
        if len(beat_times) > 1:
            tempo = 60.0 / np.median(np.diff(beat_times))
            return round(tempo, 1)
        
        # Fallback to the original method if beat tracking fails
        onset_env = librosa.onset.onset_strength(y=self.y, sr=self.sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=self.sr)[0]
        return round(tempo, 1)
    
    def get_key(self):
        """Estimate musical key"""
        chroma = librosa.feature.chroma_cqt(y=self.y, sr=self.sr)
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        key_index = np.argmax(np.sum(chroma, axis=1))
        return key_names[key_index]
    
    def get_energy(self):
        """Calculate energy level"""
        rms = librosa.feature.rms(y=self.y)[0]
        energy = np.mean(rms)
        
        # Classify energy level
        if energy < 0.02:
            return "low"
        elif energy < 0.05:
            return "medium"
        else:
            return "high"
    
    def get_spectral_centroid(self):
        """Get spectral centroid (brightness)"""
        spectral_centroids = librosa.feature.spectral_centroid(y=self.y, sr=self.sr)[0]
        return float(np.mean(spectral_centroids))
    
    def get_zero_crossing_rate(self):
        """Get zero crossing rate (percussiveness indicator)"""
        zcr = librosa.feature.zero_crossing_rate(self.y)[0]
        return float(np.mean(zcr))
    
    def get_mfcc(self):
        """Get MFCC features (timbre)"""
        mfcc = librosa.feature.mfcc(y=self.y, sr=self.sr, n_mfcc=13)
        return mfcc.mean(axis=1).tolist()
    
    def get_chroma(self):
        """Get chroma features (harmony)"""
        chroma = librosa.feature.chroma_stft(y=self.y, sr=self.sr)
        return chroma.mean(axis=1).tolist()
    
    def get_spectral_rolloff(self):
        """Get spectral rolloff (frequency distribution)"""
        rolloff = librosa.feature.spectral_rolloff(y=self.y, sr=self.sr)[0]
        return float(np.mean(rolloff))
    
    def classify_genre(self, selected_genre=None):
        """
        Classify genre based on features using a rule-based engine.
        If a genre is selected, it will be used directly.
        """
        if selected_genre and selected_genre != "Auto-detect":
            return selected_genre
            
        # --- Feature Extraction ---
        tempo = self.features.get('tempo', 0)
        energy_val = self.get_energy_value() # Get a numerical energy value
        zcr = self.features.get('zero_crossing_rate', 0)
        spectral_centroid = self.features.get('spectral_centroid', 0)

        # --- Rule Matching ---
        # Reload the genre rules module to get the latest rules
        importlib.reload(genre_rules)
        current_genre_rules = genre_rules.GENRE_RULES

        for entry in current_genre_rules:
            rules = entry.get('rules', [])
            
            # Handle OR conditions (rules as a list)
            if isinstance(rules, list):
                if any(self._match_rule(rule_set, tempo, energy_val, zcr, spectral_centroid) for rule_set in rules):
                    return entry['genre']
            # Handle AND conditions (rules as a dictionary)
            elif self._match_rule(rules, tempo, energy_val, zcr, spectral_centroid):
                return entry['genre']
                
        return "Pop" # Default genre

    def _match_rule(self, rules, tempo, energy_val, zcr, spectral_centroid):
        """Check if a set of rules matches the audio features."""
        
        # Match tempo
        if 'tempo' in rules:
            rule = rules['tempo']
            if 'min' in rule and tempo < rule['min']: return False
            if 'max' in rule and tempo > rule['max']: return False

        # Match energy
        if 'energy' in rules:
            rule = rules['energy']
            # Handle numerical ranges for energy
            if 'min' in rule and energy_val < rule['min']: return False
            if 'max' in rule and energy_val > rule['max']: return False
            # Handle string-based energy levels ('low', 'medium', 'high')
            if 'is' in rule and self.get_energy() != rule['is']: return False
            if 'not' in rule and self.get_energy() == rule['not']: return False

        # Match Zero-Crossing Rate
        if 'zero_crossing_rate' in rules:
            rule = rules['zero_crossing_rate']
            if 'min' in rule and zcr < rule['min']: return False
            if 'max' in rule and zcr > rule['max']: return False

        # Match Spectral Centroid
        if 'spectral_centroid' in rules:
            rule = rules['spectral_centroid']
            if 'min' in rule and spectral_centroid < rule['min']: return False
            if 'max' in rule and spectral_centroid > rule['max']: return False
            
        return True

    def get_energy_value(self):
        """Return the raw numerical energy value."""
        rms = librosa.feature.rms(y=self.y)[0]
        return np.mean(rms)
    
    def classify_mood(self):
        """Classify mood based on features"""
        energy = self.features['energy']
        tempo = self.features['tempo']
        key = self.features['key']
        
        # Minor keys (simplified)
        minor_keys = ['C#', 'D#', 'F#', 'G#', 'A#']
        
        if energy == "high":
            if tempo > 120:
                return "Energetic"
            return "Uplifting"
        elif energy == "low" and tempo < 90:
            if key in minor_keys:
                return "Melancholic"
            else:
                return "Calm"
        elif key in minor_keys:
            return "Emotional"
        
        return "Upbeat"
    
    def detect_instruments(self):
        """Detect likely instruments based on spectral features"""
        genre = self.classify_genre()
        instruments = []
        
        zcr = self.features['zero_crossing_rate']
        spectral_centroid = self.features['spectral_centroid']
        spectral_rolloff = self.features['spectral_rolloff']
        energy = self.features['energy']
        
        # --- Electronic Music Instrument Detection ---
        is_electronic = "Electronic" in genre or "EDM" in genre or "Hardcore" in genre or "Trance" in genre

        # Kick Drum: percussive (high zcr) and low-frequency energy (low rolloff)
        if zcr > 0.07 and spectral_rolloff < 2500 and is_electronic:
            instruments.append("kick drum")
        elif zcr > 0.08: # General percussion
            instruments.append("percussion")
        
        # Synth Pad: low brightness (low centroid) but not necessarily bassy (mid rolloff)
        if spectral_centroid < 1800 and spectral_rolloff > 2000 and energy != "high":
            instruments.append("synth pad")
        elif spectral_centroid > 3000:
            instruments.append("bright synths")
        elif spectral_centroid > 2000 and is_electronic:
            instruments.append("synth lead")
        elif spectral_centroid > 2000 and not is_electronic:
            instruments.append("electric guitar")
        
        # Bass / Sub-bass: very low frequency content
        if spectral_rolloff < 1500 and is_electronic:
            instruments.append("sub-bass")
        elif spectral_rolloff < 3000:
            instruments.append("bass")
        
        return instruments
    
    def detect_vocals(self):
        """Detect if vocals are present"""
        # Simplified vocal detection based on spectral features
        spectral_centroid = self.features['spectral_centroid']
        
        # Vocals typically have spectral centroid in 1000-4000 Hz range
        if 1000 < spectral_centroid < 4000:
            return True
        return False

    def _detect_vocal_gender(self, vocal_path):
        """Estimates vocal gender based on fundamental frequency (pitch)."""
        try:
            y, sr = librosa.load(vocal_path, sr=22050)
            
            # Use pyin to estimate fundamental frequency (F0)
            f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            
            # Get the F0 of voiced frames
            voiced_f0 = f0[voiced_flag]
            
            if len(voiced_f0) > 0:
                avg_f0 = np.mean(voiced_f0)
                # Simple thresholding: female voices are generally higher pitch
                # This is a heuristic and may not always be accurate.
                if avg_f0 > 175: # Threshold in Hz
                    return "Female"
                else:
                    return "Male"
            return None
        except Exception as e:
            print(f"Could not detect vocal gender: {e}")
            return None

    def extract_lyrics(self, model_quality='base', output_dir='temp_audio', cleanup=True):
        """
        Separates vocals from the audio and transcribes them using Whisper.
        Returns a dictionary with lyrics and vocal gender.
        """
        if not self.detect_vocals():
            return {'lyrics': None, 'gender': None}

        print("Vocal detection positive. Starting lyrics extraction...")
        vocal_path = None
        try:
            # --- 1. Separate vocals using Demucs ---
            separator = Separator()
            _, separated_tracks = separator.separate_audio_file(self.audio_path)
            
            # Find the vocal track and save it
            vocal_track = separated_tracks.get('vocals')
            if vocal_track is not None:
                os.makedirs(output_dir, exist_ok=True)
                vocal_path = os.path.join(output_dir, "vocals.wav")
                sf.write(vocal_path, vocal_track.T, separator.samplerate)
            else:
                print("Vocal separation failed, no vocal track found.")
                return {'lyrics': None, 'gender': None}

            # --- 2. Transcribe vocals using Whisper ---
            model = whisper.load_model(model_quality)
            result = model.transcribe(vocal_path)
            lyrics = result['text']

            # --- 3. Detect vocal gender from the separated track ---
            gender = self._detect_vocal_gender(vocal_path)

            return {'lyrics': lyrics, 'gender': gender}
        except Exception as e:
            print(f"An error occurred during lyrics extraction: {e}")
            return {'lyrics': None, 'gender': None}
        finally:
            # Clean up the separated audio files
            if cleanup and vocal_path and os.path.exists(os.path.dirname(vocal_path)):
                import shutil
                shutil.rmtree(os.path.dirname(vocal_path))
