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
            'zero_crossing_rate': 0.11
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
        # Test if one of the possible energy descriptors is present
        energy_descriptors = self.generator.energy_map[self.features['energy']]
        self.assertTrue(any(desc in prompt for desc in energy_descriptors))

    def test_generate_detailed_prompt(self):
        """Test the detailed prompt generation."""
        prompt = self.generator.generate_detailed()
        # Test for spectral descriptors
        spectral_descriptors = next(d for t, d in self.generator.spectral_map if self.features['spectral_centroid'] > t)
        self.assertTrue(any(desc in prompt for desc in spectral_descriptors))
        # Test for zcr descriptors
        zcr_descriptors = next(d for t, d in self.generator.zcr_map if self.features['zero_crossing_rate'] > t)
        self.assertTrue(any(desc in prompt for desc in zcr_descriptors))

    def test_generate_advanced_mode_prompts(self):
        """Test the advanced mode prompt generation."""
        prompts = self.generator.generate_advanced_mode()
        self.assertIn("[Trance]", prompts['style_prompt'])
        self.assertIn("[BPM: 128]", prompts['style_prompt'])
        self.assertIn("[Key: A# Minor]", prompts['style_prompt'])
        self.assertIn("[Vocal Style: Ethereal Female Lead]", prompts['lyrics_prompt'])
        self.assertRegex(prompts['lyrics_prompt'], r"\[Structure: Extended DJ Mix, Total Length: \d{1,2}:\d{2}]")

    def test_generate_thematic_prompt(self):
        """Test the thematic prompt generation."""
        prompt = self.generator.generate_thematic()
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 10)

    def test_generate_artist_style_prompt(self):
        """Test the artist style prompt generation."""
        prompt = self.generator.generate_artist_style()
        self.assertIn("in the style of", prompt)
        self.assertIn(self.genre, prompt)

    def test_generate_variations(self):
        """Test that all prompt variations are generated."""
        variations = self.generator.generate_variations()
        self.assertGreaterEqual(len(variations), 6) # Should be 7 if artist is found
        
        variation_names = [v['name'] for v in variations]
        self.assertIn("Basic", variation_names)
        self.assertIn("Detailed", variation_names)
        self.assertIn("Thematic", variation_names)
        self.assertIn("Artist Style", variation_names)
        self.assertIn("Advanced Mode", variation_names)

        # Check that the 'Advanced Mode' prompt is a dictionary
        advanced_prompt = next((p for p in variations if p['name'] == 'Advanced Mode'), None)
        self.assertIsNotNone(advanced_prompt)
        self.assertIsInstance(advanced_prompt['prompt'], dict)

if __name__ == '__main__':
    unittest.main()