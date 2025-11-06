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

    @patch('audio_analyzer.whisper.load_model')
    @patch('audio_analyzer.AudioAnalyzer._separate_vocals_with_demucs')
    def test_extract_lyrics(self, mock_separate, mock_load_model):
        """Test lyrics extraction workflow."""
        # Mock the vocal separation to return a dummy path
        mock_separate.return_value = 'dummy_vocals.wav'
        
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