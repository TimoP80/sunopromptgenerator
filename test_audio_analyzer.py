import unittest
import numpy as np
from unittest.mock import patch, MagicMock

from audio_analyzer import AudioAnalyzer

class TestAudioAnalyzer(unittest.TestCase):

    def setUp(self):
        """Set up a mock analyzer for each test."""
        self.analyzer = AudioAnalyzer('dummy_path.wav')
        # Mock the audio data to avoid actual file I/O
        self.analyzer.y = np.random.randn(22050 * 5)
        self.analyzer.sr = 22050
        self.analyzer.features = {
            'tempo': 128.0,
            'key': 'C',
            'energy': 'high',
            'spectral_centroid': 2500.0,
            'zero_crossing_rate': 0.08,
            'spectral_rolloff': 4000.0
        }

    def test_get_tempo(self):
        """Test tempo detection."""
        with patch('librosa.beat.beat_track') as mock_beat_track:
            # Mock the return of librosa's beat tracking
            mock_beat_track.return_value = (128.0, np.array([10, 20, 30]))
            tempo = self.analyzer.get_tempo()
            self.assertIsInstance(tempo, float)
            self.assertGreater(tempo, 0)

    def test_tempo_octave_correction(self):
        """Test the octave correction for high-BPM tracks."""
        # Mock a high-energy, bright track where tempo might be halved
        self.analyzer.features['energy'] = 'high'
        self.analyzer.features['spectral_centroid'] = 2300.0
        
        with patch('librosa.beat.beat_track') as mock_beat_track:
            # Simulate a detected tempo of 100, which should be doubled
            mock_beat_track.return_value = (100.0, np.array([]))
            corrected_tempo = self.analyzer.get_tempo()
            self.assertEqual(corrected_tempo, 200.0)

    def test_classify_genre_techno(self):
        """Test genre classification for Techno."""
        self.analyzer.features['tempo'] = 130
        genre = self.analyzer.classify_genre()
        self.assertEqual(genre, "Techno")

    def test_classify_genre_default(self):
        """Test default genre classification."""
        self.analyzer.features['tempo'] = 100
        genre = self.analyzer.classify_genre()
        self.assertEqual(genre, "Pop")

    def test_classify_mood_energetic(self):
        """Test mood classification for Energetic."""
        self.analyzer.features['energy'] = 'high'
        self.analyzer.features['tempo'] = 130
        mood = self.analyzer.classify_mood()
        self.assertEqual(mood, "Energetic")

    @patch('audio_analyzer.mutagen.File')
    def test_extract_extended_metadata(self, mock_mutagen_file):
        """Test extracting extended metadata like BPM and key from tags."""
        # Mock the mutagen File object
        mock_audio = MagicMock()
        mock_audio.info.length = 300
        mock_audio.info.sample_rate = 44100
        mock_audio.info.channels = 2
        
        # Mock the 'easy' interface for mutagen
        mock_mutagen_file.return_value = {
            'bpm': ['128.0'],
            'initialkey': ['Gm']
        }

        # Mock soundfile to avoid file I/O
        with patch('audio_analyzer.sf.SoundFile') as mock_soundfile:
            mock_sf_instance = MagicMock()
            mock_sf_instance.__enter__.return_value.samplerate = 44100
            mock_sf_instance.__enter__.return_value.channels = 2
            mock_sf_instance.__enter__.return_value.frames = 22050 * 5 # 5 seconds
            mock_soundfile.return_value = mock_sf_instance

            metadata = self.analyzer.extract_metadata()
            self.assertEqual(metadata.get('bpm'), 128.0)
            self.assertEqual(metadata.get('key'), 'Gm')

    @patch('audio_analyzer.whisper.load_model')
    @patch('audio_analyzer.Separator.separate_audio_file')
    def test_extract_lyrics(self, mock_separate, mock_load_model):
        """Test lyrics extraction workflow."""
        # Mock the vocal separation to return a dummy path
        # Mock the separator to return a tuple with a dictionary containing vocal data
        mock_separate.return_value = (None, {'vocals': np.array([0.1, 0.2, 0.3])})
        
        # Mock the whisper model and its transcribe method
        mock_transcribe = MagicMock()
        mock_transcribe.transcribe.return_value = {'text': 'test lyrics'}
        mock_load_model.return_value = mock_transcribe

        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            # Mock vocal gender detection to simplify the test
            with patch.object(self.analyzer, '_detect_vocal_gender', return_value='Female'):
                result = self.analyzer.extract_lyrics()
                self.assertEqual(result['lyrics'], 'test lyrics')
                self.assertEqual(result['gender'], 'Female')

if __name__ == '__main__':
    unittest.main()