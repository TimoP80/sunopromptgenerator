import random
import json

class PromptGenerator:
    """Generates Suno v5 compatible prompts from audio features"""
    
    def __init__(self, features, genre, mood, instruments, has_vocals, lyrics=None, vocal_gender=None):
        self.features = features
        self.genre = genre
        self.mood = mood
        self.instruments = instruments
        self.has_vocals = has_vocals
        self.lyrics = lyrics
        self.vocal_gender = vocal_gender
        self.genre_rules = self._load_genre_rules()

        # Data for more varied prompts
        self.tempo_map = [
            (180, ["ultra-fast", "200+ bpm", "speedcore pace"]),
            (170, ["hyper-speed", "breakneck speed", "blistering pace", "frenetic rhythm"]),
            (160, ["very fast", "drum and bass tempo", "jungle rhythm"]),
            (150, ["fast-paced", "high-velocity", "driving beat", "rapid-fire rhythm"]),
            (140, ["fast trance tempo", "hardstyle pace"]),
            (130, ["up-tempo", "energetic rhythm", "brisk pace", "four-on-the-floor"]),
            (120, ["house tempo", "dance groove"]),
            (110, ["moderate tempo", "steady groove", "medium pace", "walking pace"]),
            (100, ["hip-hop tempo", "boom-bap groove"]),
            (90, ["mid-tempo", "relaxed rhythm", "laid-back feel", "chilled groove"]),
            (80, ["slow jam tempo", "reggae skank"]),
            (70, ["slow-groove", "unhurried pace", "gentle rhythm", "downtempo"]),
            (60, ["ballad tempo", "slow and steady"]),
            (0, ["very slow", "glacial pace", "ambient rhythm", "larghissimo"])
        ]
        self.energy_map = {
            "high": ["high-energy", "explosive", "intense", "powerful", "peak-time", "frenetic"],
            "medium": ["driving", "flowing", "persistent", "steady energy", "cruising"],
            "low": ["mellow", "calm", "subtle", "gentle energy", "after-hours", "background"]
        }
        self.spectral_map = [
            (3000, ["bright", "crystal-clear", "sharp highs", "airy", "sparkling"]),
            (1500, ["warm", "full-bodied", "rich mids", "rounded", "present"]),
            (0, ["dark", "bassy", "deep lows", "sub-heavy", "booming"])
        ]
        self.zcr_map = [
            (0.1, ["crisp", "textured", "buzzy", "noisy", "gritty"]),
            (0.05, ["smooth", "clean", "pure tone", "polished"]),
            (0, ["soft", "muted", "rounded", "pillowy"])
        ]
        self.artist_map = {
            "Trance": ["Armin van Buuren", "Paul van Dyk", "Above & Beyond", "Ferry Corsten"],
            "House": ["Frankie Knuckles", "Daft Punk", "Swedish House Mafia", "deadmau5", "Disclosure"],
            "Techno": ["Richie Hawtin", "Carl Cox", "Adam Beyer", "Amelie Lens", "Jeff Mills"],
            "Drum & Bass": ["Goldie", "Andy C", "Pendulum", "Noisia", "Sub Focus"],
            "Hardcore/Gabber": ["Angerfist", "Partyraiser", "Dr. Peacock", "Sefa"],
            "Hardstyle": ["Headhunterz", "Wildstylez", "Brennan Heart", "Coone"],
            "Pop": ["Taylor Swift", "Dua Lipa", "The Weeknd", "Billie Eilish"]
        }

        # --- V5 Prompt Enhancement Data ---
        self.instrument_texture_map = {
            "Synth": ["analog synth pad", "reverb-drenched pluck", "spectral keys", "arpeggiated synth line", "warm analog synth"],
            "Drums": ["punchy drum machine", "gated drums", "dusty vinyl texture drums", "four-on-the-floor beat", "breakbeat rhythm"],
            "Bass": ["deep sub-bass", "funky bassline", "rolling bassline", "acid bassline"],
            "Guitar": ["acoustic guitar", "distorted electric guitar", "clean electric guitar riff"],
            "Piano": ["grand piano melody", "honky-tonk piano", "rhodes piano chords"],
            "Strings": ["string quartet", "cinematic strings section", "pizzicato strings"]
        }
        self.production_style_map = [
            "warm and intimate", "aggressive and driving", "ethereal and ambient",
            "punchy and modern mix", "wide stereo field", "vintage tape hiss",
            "lo-fi aesthetic", "crisp production", "live room reverb", "minimalist groove",
            "cinematic sound design", "raw and gritty"
        ]
        self.vocal_style_map = {
            "male": {
                "high": ["powerful male tenor", "energetic male vocal", "soaring male lead"],
                "medium": ["smooth male vocal", "baritone rap-style vocal", "soulful male vocal"],
                "low": ["soft breathy male vocal", "deep baritone vocal", "spoken word male voice"]
            },
            "female": {
                "high": ["ethereal female vocal", "powerful soprano lead", "breathy female vocal"],
                "medium": ["soulful female alto", "pop-style female vocal", "R&B female lead"],
                "low": ["soft female vocal", "contralto vocal", "intimate female whisper"]
            }
        }

    def _load_genre_rules(self):
        """Loads genre rules from the external JSON file."""
        try:
            with open("genre_rules.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _get_random_descriptor(self, value, descriptor_map):
        """Gets a random descriptor from a map based on a value."""
        for threshold, descriptors in descriptor_map:
            if value > threshold:
                return random.choice(descriptors)
        return ""

    def generate(self):
        """Generate a Suno v5 compatible prompt"""
        prompt_parts = []
        
        # --- Core Elements ---
        # --- Core Elements (V5 Enhanced) ---
        prompt_parts.append(self.genre)
        prompt_parts.append(self.mood.lower())
        
        # --- Add texture from genre rules ---
        genre_rule = next((rule for rule in self.genre_rules if rule['genre'] == self.genre), None)
        if genre_rule and 'texture' in genre_rule:
            prompt_parts.append(genre_rule['texture'])
        
        # --- Rhythmic Elements ---
        tempo = self.features.get('tempo', 120)
        tempo_descriptor = self._get_random_descriptor(tempo, self.tempo_map)
        if tempo_descriptor:
            prompt_parts.append(tempo_descriptor)
        prompt_parts.append(f"{int(tempo)} bpm")
        
        # --- Textural & Timbral Elements ---
        energy = self.features.get('energy', 'medium')
        if energy in self.energy_map:
            prompt_parts.append(random.choice(self.energy_map[energy]))
            
        spectral_centroid = self.features.get('spectral_centroid', 1500)
        spectral_descriptor = self._get_random_descriptor(spectral_centroid, self.spectral_map)
        if spectral_descriptor:
            prompt_parts.append(spectral_descriptor)

        # --- Instrumentation (V5 Enhanced) ---
        if self.instruments:
            textured_instruments = [random.choice(self.instrument_texture_map.get(inst, [inst])) for inst in self.instruments]
            prompt_parts.extend(textured_instruments)
        
        # --- Vocals (V5 Enhanced) ---
        if self.has_vocals and self.vocal_gender:
            energy_level = self.features.get('energy', 'medium')
            energy_key = 'high' if energy_level == 'high' else ('low' if energy_level == 'low' else 'medium')
            
            vocal_desc = random.choice(self.vocal_style_map.get(self.vocal_gender.lower(), {}).get(energy_key, [f"{self.vocal_gender.lower()} vocals"]))
            prompt_parts.append(vocal_desc)
        elif self.has_vocals:
            prompt_parts.append("vocals")
        else:
            prompt_parts.append("instrumental")
        
        # --- Harmonic Elements ---
        key = self.features.get('key', 'C')
        prompt_parts.append(f"in the key of {key}")
        
        # --- Final Touches ---
        prompt_parts.append(random.choice(self.production_style_map))
        
        # Join all parts, ensuring no duplicates and filtering empty strings
        unique_parts = list(dict.fromkeys(filter(None, prompt_parts)))
        prompt = ", ".join(unique_parts)
        
        return prompt
    
    def generate_detailed(self):
        """Generate a more detailed prompt with additional descriptors"""
        base_prompt = self.generate()
        
        # Add style descriptors based on features
        style_descriptors = []
        
        # Spectral characteristics
        spectral_centroid = self.features.get('spectral_centroid', 1500)
        spectral_descriptor = self._get_random_descriptor(spectral_centroid, self.spectral_map)
        if spectral_descriptor:
            style_descriptors.append(spectral_descriptor)

        # Zero crossing rate (texture)
        zcr = self.features.get('zero_crossing_rate', 0.05)
        zcr_descriptor = self._get_random_descriptor(zcr, self.zcr_map)
        if zcr_descriptor:
            style_descriptors.append(zcr_descriptor)

        if style_descriptors:
            base_prompt += f", {', '.join(style_descriptors)}"
        
        # --- Add notes from genre rules ---
        genre_rule = next((rule for rule in self.genre_rules if rule['genre'] == self.genre), None)
        if genre_rule and 'notes' in genre_rule:
            base_prompt += f", ({genre_rule['notes']})"
            
        return base_prompt
    
    def _calculate_structure_timings(self, structure_definition):
        """Calculates timestamps for a given song structure based on BPM."""
        bpm = self.features.get('tempo', 120)
        total_seconds = 0
        timed_structure = []

        for section, bars in structure_definition:
            # Calculate duration: (bars * 4 beats/bar) / (BPM beats/min) * 60 sec/min
            duration = (bars * 4 * 60) / bpm
            
            start_time = f"{int(total_seconds // 60)}:{int(total_seconds % 60):02d}"
            total_seconds += duration
            end_time = f"{int(total_seconds // 60)}:{int(total_seconds % 60):02d}"
            
            timed_structure.append(f"{section} – {start_time}–{end_time}")
        return timed_structure, f"{int(total_seconds // 60)}:{int(total_seconds % 60):02d}"

    def _generate_structured_lyrics_template(self):
        """
        Generates a detailed, structured lyrics template based on genre,
        inserting actual lyrics if available and supporting longer structures.
        """
        key = self.features.get('key', 'C')
        key_name = key.replace('m', '')
        key_mode = "Minor" if 'm' in key else "Major"

        # --- 1. Metadata Block ---
        metadata = [
            f"[TITLE: (A song about {self.mood})]",
            f"[ARTIST STYLE: A mix of {random.choice(self.artist_map.get(self.genre, ['...']))} and modern pop]",
            f"[Genre: {self.genre}, extended mix, DJ friendly 5-minute version]",
            f"[Mood: {self.mood}]",
            "[Era: 2020s]",
            f"[Energy: {self.features.get('energy', 'medium')}]",
            f"[BPM: {int(self.features.get('tempo', 120))}]",
            f"[Key: {key_name} {key_mode}]",
        ]
        if self.has_vocals:
            vocal_style = "Ethereal" if self.mood in ["Calm", "Melancholic"] else "Powerful"
            if self.vocal_gender:
                metadata.append(f"[Vocal Style: {vocal_style} {self.vocal_gender} Lead]")
            else:
                metadata.append(f"[Vocal Style: {vocal_style} Lead Vocals]")
            metadata.append("[Vocal Effect: Reverb + Delay]")
        if self.instruments:
            metadata.append(f"[Instrumentation: {', '.join(self.instruments)}]")
        
        metadata.append("[Production: Wide Stereo, Clean Master]")

        # --- 2. Dynamic Lyric & Structure Generation ---
        lyric_themes = {
            "Energetic": [
                "overcoming a great challenge", "the feeling of a massive celebration",
                "a high-speed chase through a futuristic city", "the peak of a mountain climb"
            ],
            "Uplifting": [
                "finding hope after a dark time", "a community coming together",
                "the beauty of a sunrise", "a message of unity and love"
            ],
            "Melancholic": [
                "a reflection on a lost love", "the bittersweet feeling of a past memory",
                "walking alone in a rainy city", "a quiet moment of introspection"
            ],
            "Calm": [
                "a peaceful walk through a forest", "the gentle lapping of waves on a shore",
                "a quiet cup of tea on a lazy Sunday", "watching the stars on a clear night"
            ],
            "Emotional": [
                "a heartfelt confession", "the pain of a difficult choice",
                "a story of love and loss", "a powerful moment of self-discovery"
            ],
            "Upbeat": [
                "a carefree summer day", "dancing with friends at a festival",
                "the excitement of a new beginning", "a joyful road trip"
            ]
        }
        
        lyric_theme = f"a story about {self.mood.lower()}"
        if self.mood in lyric_themes:
            lyric_theme = random.choice(lyric_themes[self.mood])

        verse_1_lyrics = self.lyrics if self.lyrics else f"({lyric_theme})"
        chorus_lyrics = "(A powerful, memorable chorus that captures the main theme)"

        # --- Define multiple song structures ---
        structures = {
            "Verse-Chorus": [
                "\n[INTRO]", "[Instrumental]", "\n[VERSE 1]", verse_1_lyrics,
                "\n[CHORUS]", chorus_lyrics, "\n[VERSE 2]", f"(A second verse that expands on the theme)",
                "\n[CHORUS]", chorus_lyrics, "\n[BRIDGE]", "(A change of pace, different chords or melody)",
                "\n[CHORUS]", chorus_lyrics, "\n[OUTRO]", "(Fade out or a final impactful chord)"
            ],
            "AABA": [
                "\n[PART A1]", verse_1_lyrics, "\n[PART A2]", "(Similar melody, different lyrics)",
                "\n[PART B - BRIDGE]", "(A contrasting section, new ideas)", "\n[PART A3]", "(Return to the main theme, a powerful conclusion)"
            ],
            "Storytelling Ballad": [
                "\n[INTRO]", "(Gentle instrumental opening)", "\n[VERSE 1]", "(Introduce the characters and setting)",
                "\n[VERSE 2]", "(Develop the plot, introduce a conflict)", "\n[CHORUS]", "(The emotional core of the story)",
                "\n[VERSE 3]", "(The climax of the story)", "\n[BRIDGE]", "(A moment of reflection or a twist)",
                "\n[OUTRO]", "(The resolution, a final thought)"
            ],
            "Electronic DJ Mix": [
                ("\n[INTRO", 16), ("[Instrumental]", 0), ("(Atmospheric pads, reverb-drenched pluck, rolling kick drum)", 0),
                ("\n[BUILDUP 1", 32), ("(Main synth teases melody, filter sweeps, risers build tension, gated percussion)", 0),
                ("\n[VERSE 1" if self.has_vocals else "\n[MAIN SECTION", 16), (verse_1_lyrics if self.has_vocals else "(Instrumental with main riff, evolving filter automation, deep sub-bass)", 0),
                ("\n[BREAKDOWN", 32), ("(Pads open up, melody emerges. Ethereal textures, wide stereo field)", 0),
                ("\n[BUILDUP 2", 32), ("(Snare roll tension, risers, white noise swell, punchy drums)", 0),
                ("\n[DROP / CHORUS", 32), (chorus_lyrics if self.has_vocals else "(Big lead melody, full beat, hands-in-the-air moment, analog pad)", 0),
                ("\n[OUTRO", 32), ("(Pads and bassline slowly filter down, fade out with vintage tape hiss)", 0)
            ]
        }

        is_electronic = any(g in self.genre for g in ["Trance", "EDM", "Hardcore", "Electronic", "Techno", "House"])
        
        if is_electronic:
            chosen_structure_name = "Electronic DJ Mix"
            structure_def = structures[chosen_structure_name]
            timed_structure, total_duration = self._calculate_structure_timings(structure_def)
            metadata.append(f"[Structure: {chosen_structure_name}, Total Length: {total_duration}]")
            
            final_structure = []
            i = 0
            while i < len(structure_def):
                section_name = structure_def[i][0]
                if section_name.startswith("\n["):
                    final_structure.append(timed_structure.pop(0) + "]")
                    i += 1
                    while i < len(structure_def) and not structure_def[i][0].startswith("\n["):
                        final_structure.append(structure_def[i][0])
                        i += 1
                else:
                    i += 1
            structure = final_structure
        else:
            # Exclude DJ mix for non-electronic genres
            non_dj_structures = {k: v for k, v in structures.items() if k != "Electronic DJ Mix"}
            chosen_structure_name = random.choice(list(non_dj_structures.keys()))
            structure = non_dj_structures[chosen_structure_name]
            metadata.append(f"[Structure: {chosen_structure_name}]")

        # Filter out empty lines from the structure
        structure = [line for line in structure if isinstance(line, str) and line.strip()]
        return "\n".join(metadata) + "\n" + "\n".join(structure)

    def generate_advanced_mode(self):
        """Generates separate style and lyrics prompts for Suno's Custom Mode."""
        
        # 1. Generate the meta-tag based Style Prompt
        key = self.features.get('key', 'C')
        key_name = key.replace('m', '')
        key_mode = "Minor" if 'm' in key else "Major"
        
        style_tags = [
            f"[{self.genre}]",
            f"[{self.mood}]",
            f"[BPM: {int(self.features.get('tempo', 120))}]",
            f"[Key: {key_name} {key_mode}]",
            f"[{self.features.get('energy', 'medium')} energy]"
        ]
        if self.instruments:
            style_tags.append(f"[Instrumentation: {', '.join(self.instruments)}]")
        
            
        style_prompt = " ".join(style_tags)
        
        # 2. Generate the new structured lyrics template
        lyrics_prompt = self._generate_structured_lyrics_template()
        return {"style_prompt": style_prompt, "lyrics_prompt": lyrics_prompt}


    def generate_thematic(self):
        """Generates a prompt based on a theme or scene."""
        scenarios = [
            "a late-night drive through a neon-lit city",
            "a futuristic sci-fi movie scene",
            "a massive festival mainstage",
            "watching a sunrise over the ocean",
            "a dark, underground club",
            "an epic fantasy battle",
            "a retro 80s arcade",
            "a peaceful walk in a rainy forest",
            "a high-speed chase sequence"
        ]
        feelings = [
            "epic and cinematic", "introspective and thoughtful", "euphoric and hands-in-the-air",
            "dark and mysterious", "joyful and carefree", "hypnotic and driving"
        ]
        
        theme = f"A soundtrack for {random.choice(scenarios)}, {self.genre}, {self.mood.lower()}, {random.choice(feelings)}"
        return theme

    def generate_artist_style(self):
        """Generates a prompt in the style of a famous artist."""
        if self.genre in self.artist_map:
            artist = random.choice(self.artist_map[self.genre])
            return f"{self.genre} in the style of {artist}, {self.mood.lower()}, {self.features['energy']} energy"
        return None # Return None if no artists are defined for the genre

    def generate_refinement_prompt(self):
        """
        Generates a highly specific, prescriptive prompt for refining a generation,
        locking in the key characteristics of the analyzed audio, based on ChatGPT's feedback loop suggestion.
        """
        # --- 1. Load analysis data ---
        tempo = self.features.get('tempo', 120)
        key = self.features.get('key', 'C')
        energy = self.features.get('energy', 'medium')
        centroid = self.features.get('spectral_centroid', 1500)
        
        # --- 2. Build refinement descriptors ---
        tempo_desc = f"{tempo:.1f} BPM {energy} rhythm"
        key_desc = f"in the key of {key}"
        energy_desc = f"{energy} loudness profile"
        brightness_desc = "bright and crisp highs" if centroid > 2500 else "dark, warm tone"
        instrument_list = ", ".join(self.instruments)

        # --- 3. Assemble refinement prompt text ---
        refinement_prompt = (
            f"Generate a {self.genre} segment at {tempo_desc}, {key_desc}.\n"
            f"Keep {energy_desc} with {brightness_desc}.\n"
            f"Feature {instrument_list}.\n"
            f"Mood: {self.mood}.\n"
            "Maintain tempo and energy consistency with the previous render."
        )

        # --- 4. Optional: select length and purpose ---
        bars = random.choice([4, 8, 16])
        purpose = "drop transition" if energy == "high" else "intro fill"
        title = f"{self.genre} Refinement ({bars}-bar {purpose})"

        # --- 5. Wrap into a final descriptive block for clarity ---
        final_output = (
            f"--- {title} ---\n"
            f"[Prompt]:\n{refinement_prompt}\n\n"
            f"[Suno Metadata Suggestions]:\n"
            f"  - Title: {title}\n"
            f"  - Styles: {self.genre}, {int(tempo)} BPM, {self.mood}\n"
            f"  - Key: {key}\n"
            f"  - BPM: {int(tempo)}"
        )
        
        return final_output

    def generate_variations(self):
        """Generate multiple prompt variations"""
        variations = []
        
        # Variation 1: Basic
        variations.append({
            "name": "Basic",
            "prompt": self.generate()
        })
        
        # Variation 2: Detailed
        variations.append({
            "name": "Detailed",
            "prompt": self.generate_detailed()
        })
        
        # Variation 3: Style-focused
        style_prompt = f"{self.genre}, {self.mood.lower()}, {', '.join(self.instruments[:2])}"
        if self.has_vocals:
            style_prompt += ", vocals"
        variations.append({
            "name": "Style-Focused",
            "prompt": style_prompt
        })
        
        # Variation 4: Tempo-focused
        tempo = self.features.get('tempo', 120)
        tempo_prompt = f"{self.genre}, {int(tempo)} bpm, {self.features.get('energy', 'medium')} energy"
        if self.mood:
            tempo_prompt += f", {self.mood.lower()}"
        variations.append({
            "name": "Tempo-Focused",
            "prompt": tempo_prompt
        })

        # Variation 5: Thematic
        variations.append({
            "name": "Thematic",
            "prompt": self.generate_thematic()
        })

        # Variation 6: Artist Style
        artist_prompt = self.generate_artist_style()
        if artist_prompt:
            variations.append({
                "name": "Artist Style",
                "prompt": artist_prompt
            })

        # Variation 7: Refinement Prompt (New)
        variations.append({
            "name": "Refinement Prompt",
            "prompt": self.generate_refinement_prompt()
        })

        # Variation 8: Advanced Mode
        advanced_prompts = self.generate_advanced_mode()
        variations.append({
            "name": "Advanced Mode",
            "prompt": advanced_prompts # This will be a dictionary
        })
        
        return variations
