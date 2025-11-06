import unittest
import json
from unittest.mock import patch
from io import BytesIO

from app import app

class AppTestCase(unittest.TestCase):

    def setUp(self):
        """Set up a test client for each test."""
        self.app = app.test_client()
        self.app.testing = True

    def test_health_check(self):
        """Test the health check endpoint."""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    @patch('app.AudioAnalyzer')
    @patch('app.PromptGenerator')
    def test_analyze_audio_success(self, MockPromptGenerator, MockAudioAnalyzer):
        """Test the analyze endpoint with a successful audio upload."""
        # Mock the analyzer and generator
        mock_analyzer_instance = MockAudioAnalyzer.return_value
        mock_analyzer_instance.analyze.return_value = {'tempo': 120, 'key': 'C', 'energy': 'high'}
        mock_analyzer_instance.classify_genre.return_value = 'Pop'
        mock_analyzer_instance.classify_mood.return_value = 'Happy'
        mock_analyzer_instance.detect_instruments.return_value = ['guitar']
        mock_analyzer_instance.detect_vocals.return_value = False

        mock_generator_instance = MockPromptGenerator.return_value
        mock_generator_instance.generate_variations.return_value = [{'name': 'Basic', 'prompt': 'Pop, Happy'}]

        # Create a dummy file for upload
        data = {
            'audio': (BytesIO(b"dummy audio data"), 'test.wav')
        }

        response = self.app.post('/api/analyze', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 200)
        # The response is a stream, so we can't easily check the content here.
        # A more advanced test would involve consuming the stream.

    def test_analyze_audio_no_file(self):
        """Test the analyze endpoint with no file provided."""
        response = self.app.post('/api/analyze', content_type='multipart/form-data', data={})
        self.assertEqual(response.status_code, 200)
        # We expect the stream to contain an error message.

if __name__ == '__main__':
    unittest.main()