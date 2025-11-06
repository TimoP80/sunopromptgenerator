import unittest
from prompt_generator import PromptGenerator

class TestPromptGenerator(unittest.TestCase):

    def setUp(self):
        """Set up a generator for each test."""
        self.features = {
            'tempo': 128.0,
            'key': 'A#',
            'energy': 'high',
            'spectral_centroid': 3200.0,
            'zero_crossing_rate': 0.09
        }
        self.genre = 'Trance'
        self.mood = 'Energetic'
        self.instruments = ['synth lead', 'kick drum', 'sub-bass']
        self.has_vocals = True
        self.lyrics = "This is a test lyric."
        self.vocal_gender = 'Female'
        self.generator = PromptGenerator(
            self.features, self.genre, self.mood, self.instruments,
            self.has_vocals, self.lyrics, self.vocal_gender
        )

    def test_generate_basic_prompt(self):
        """Test the basic prompt generation."""
        prompt = self.generator.generate()
        self.assertIn(self.genre, prompt)
        self.assertIn(self.mood.lower(), prompt)
        self.assertIn("128 bpm", prompt)
        self.assertIn("vocals", prompt)

    def test_generate_detailed_prompt(self):
        """Test the detailed prompt generation."""
        prompt = self.generator.generate_detailed()
        self.assertIn("bright", prompt)
        self.assertIn("crisp", prompt)

    def test_generate_advanced_mode_prompts(self):
        """Test the advanced mode prompt generation."""
        prompts = self.generator.generate_advanced_mode()
        self.assertIn("[Trance]", prompts['style_prompt'])
        self.assertIn("[BPM: 128]", prompts['style_prompt'])
        self.assertIn("[Key: A# Minor]", prompts['style_prompt'])
        self.assertIn("[Vocal Style: Ethereal Female Lead]", prompts['lyrics_prompt'])
        self.assertIn("[STRUCTURE: Extended DJ Mix]", prompts['lyrics_prompt'])

    def test_generate_variations(self):
        """Test that all prompt variations are generated."""
        variations = self.generator.generate_variations()
        self.assertEqual(len(variations), 5)
        # Check that the 'Advanced Mode' prompt is a dictionary
        advanced_prompt = next((p for p in variations if p['name'] == 'Advanced Mode'), None)
        self.assertIsNotNone(advanced_prompt)
        self.assertIsInstance(advanced_prompt['prompt'], dict)

if __name__ == '__main__':
    unittest.main()