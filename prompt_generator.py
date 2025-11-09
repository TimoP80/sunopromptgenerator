import random

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

        # Data for more varied prompts
        self.tempo_map = [
            (170, ["hyper-speed", "breakneck speed", "blistering pace"]),
            (150, ["fast-paced", "high-velocity", "driving beat"]),
            (130, ["up-tempo", "energetic rhythm", "brisk pace"]),
            (110, ["moderate tempo", "steady groove", "medium pace"]),
            (90, ["mid-tempo", "relaxed rhythm", "laid-back feel"]),
            (70, ["slow-groove", "unhurried pace", "gentle rhythm"]),
            (0, ["ballad tempo", "very slow", "glacial pace"])
        ]
        self.energy_map = {
            "high": ["high-energy", "explosive", "intense", "powerful"],
            "medium": ["driving", "flowing", "persistent", "steady energy"],
            "low": ["mellow", "calm", "subtle", "gentle energy"]
        }
        self.spectral_map = [
            (3000, ["bright", "crystal-clear", "sharp highs"]),
            (1500, ["warm", "full-bodied", "rich mids"]),
            (0, ["dark", "bassy", "deep lows"])
        ]
        self.zcr_map = [
            (0.1, ["crisp", "textured", "buzzy"]),
            (0.05, ["smooth", "clean", "pure tone"]),
            (0, ["soft", "muted", "rounded"])
        ]
        self.artist_map = {
            "Trance": ["Armin van Buuren", "Paul van Dyk", "Above & Beyond"],
            "House": ["Frankie Knuckles", "Daft Punk", "Swedish House Mafia"],
            "Techno": ["Richie Hawtin", "Carl Cox", "Adam Beyer"],
            "Drum & Bass": ["Goldie", "Andy C", "Pendulum"],
            "Hardcore/Gabber": ["Angerfist", "Partyraiser", "Dr. Peacock"]
        }

    def _get_random_descriptor(self, value, descriptor_map):
        """Gets a random descriptor from a map based on a value."""
        for threshold, descriptors in descriptor_map:
            if value > threshold:
                return random.choice(descriptors)
        return ""

    def generate(self):
        """Generate a Suno v5 compatible prompt"""
        prompt_parts = []
        
        # Add genre
        prompt_parts.append(self.genre)
        
        # Add mood/atmosphere
        prompt_parts.append(self.mood.lower())
        
        # Add tempo descriptor
        tempo = self.features['tempo']
        tempo_descriptor = self._get_random_descriptor(tempo, self.tempo_map)
        if tempo_descriptor:
            prompt_parts.append(tempo_descriptor)

        # Add BPM if specific
        if tempo > 100:
            prompt_parts.append(f"{int(tempo)} bpm")
        
        # Add energy descriptor
        energy = self.features['energy']
        if energy in self.energy_map:
            prompt_parts.append(random.choice(self.energy_map[energy]))

        # Add instruments
        if self.instruments:
            instrument_str = ", ".join(self.instruments[:3])  # Limit to 3
            prompt_parts.append(instrument_str)
        
        # Add vocal characteristics
        if self.has_vocals:
            # You could enhance this with gender detection
            prompt_parts.append("vocals")
        else:
            prompt_parts.append("instrumental")
        
        # Add key if relevant
        key = self.features['key']
        prompt_parts.append(f"in {key}")
        
        # Join all parts
        prompt = ", ".join(filter(None, prompt_parts))
        
        return prompt
    
    def generate_detailed(self):
        """Generate a more detailed prompt with additional descriptors"""
        base_prompt = self.generate()
        
        # Add style descriptors based on features
        style_descriptors = []
        
        # Spectral characteristics
        spectral_centroid = self.features['spectral_centroid']
        spectral_descriptor = self._get_random_descriptor(spectral_centroid, self.spectral_map)
        if spectral_descriptor:
            style_descriptors.append(spectral_descriptor)

        # Zero crossing rate (texture)
        zcr = self.features['zero_crossing_rate']
        zcr_descriptor = self._get_random_descriptor(zcr, self.zcr_map)
        if zcr_descriptor:
            style_descriptors.append(zcr_descriptor)

        if style_descriptors:
            return f"{base_prompt}, {', '.join(style_descriptors)}"
        
        return base_prompt
    
    def _calculate_structure_timings(self, structure_definition):
        """Calculates timestamps for a given song structure based on BPM."""
        bpm = self.features['tempo']
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
        key = self.features['key']
        minor_keys = ['C#', 'D#', 'F#', 'G#', 'A#']
        key_mode = "Minor" if key in minor_keys else "Major"

        # --- 1. Metadata Block ---
        metadata = [
            f"[TITLE: (A song about {self.mood})]",
            f"[ARTIST STYLE: A mix of {random.choice(self.artist_map.get(self.genre, ['...']))} and modern pop]",
            f"[Genre: {self.genre}, extended mix, DJ friendly 5-minute version]",
            f"[Mood: {self.mood}]",
            "[Era: 2020s]",
            f"[Energy: {self.features['energy']}]",
            f"[BPM: {int(self.features['tempo'])}]",
            f"[Key: {key} {key_mode}]",
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

        # --- 2. Structure Block (Genre-dependent and longer) ---
        is_electronic = any(g in self.genre for g in ["Trance", "EDM", "Hardcore", "Electronic", "Techno", "House"])
        
        # --- Dynamic Lyric Placeholders ---
        lyric_theme = f"a story about {self.mood.lower()}"
        if self.mood == "Energetic":
            lyric_theme = "lyrics about overcoming challenges or celebrating a victory"
        elif self.mood == "Melancholic":
            lyric_theme = "a reflection on lost love or a past memory"

        verse_1_lyrics = self.lyrics if self.lyrics else f"({lyric_theme})"
        chorus_lyrics = "(A powerful, memorable chorus that captures the main theme)"

        structure = []
        if is_electronic:
            # Define structure with bars for timing calculation
            structure_def = [
                ("\n[INTRO", 16),
                ("[Instrumental]", 0),
                ("Atmospheric pads, soft arpeggios, rolling kick drum.", 0),
                ("\n[BUILDUP 1", 32),
                ("Main synth teases melody, filter sweeps, risers build tension.", 0),
                ("\n[VERSE 1" if self.has_vocals else "\n[MAIN SECTION", 16),
                (verse_1_lyrics if self.has_vocals else "[Instrumental] Main riff, evolving filter automation.", 0),
                ("\n[BREAKDOWN", 32),
                ("Pads open up, melody emerges. Ethereal textures.", 0),
                ("\n[BUILDUP 2", 32),
                ("Snare roll tension, risers, white noise swell.", 0),
                ("\n[DROP / CHORUS", 32),
                (chorus_lyrics if self.has_vocals else "[Instrumental] Big lead melody, full beat, hands-in-the-air moment.", 0),
                ("\n[OUTRO", 32),
                ("Pads and bassline slowly filter down, fade out.", 0)
            ]
            
            timed_structure, total_duration = self._calculate_structure_timings(structure_def)
            metadata.append(f"[Structure: Extended DJ Mix, Total Length: {total_duration}]")
            
            # Reconstruct the final structure text with timings
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

        else: # Default to a Pop/Rock structure
            metadata.append("[Structure: Standard Song]")
            structure = [
                "\n[INTRO]",
                "[Instrumental]",
                "\n[VERSE 1]",
                verse_1_lyrics,
                "\n[PRE-CHORUS]",
                "Builds tension leading to the chorus...",
                "\n[CHORUS]",
                chorus_lyrics,
                "\n[VERSE 2]",
                f"(A second verse that expands on {lyric_theme})",
                "\n[CHORUS]",
                chorus_lyrics,
                "\n[BRIDGE]",
                "A change of pace, different chords or melody...",
                "\n[GUITAR SOLO]" if "guitar" in " ".join(self.instruments) else "",
                "" if "guitar" not in " ".join(self.instruments) else "Melodic and emotional solo.",
                "\n[CHORUS]",
                chorus_lyrics,
                "\n[OUTRO]",
                "Fade out or a final impactful chord."
            ]

        # Filter out empty lines from the structure
        structure = [line for line in structure if line.strip()]
        return "\n".join(metadata) + "\n" + "\n".join(structure)

    def generate_advanced_mode(self):
        """Generates separate style and lyrics prompts for Suno's Custom Mode."""
        
        # 1. Generate the meta-tag based Style Prompt
        key = self.features['key']
        minor_keys = ['C#', 'D#', 'F#', 'G#', 'A#']
        key_mode = "Minor" if key in minor_keys else "Major"
        
        style_tags = [
            f"[{self.genre}]",
            f"[{self.mood}]",
            f"[BPM: {int(self.features['tempo'])}]",
            f"[Key: {key} {key_mode}]",
            f"[{self.features['energy']} energy]"
        ]
        if self.instruments:
            style_tags.append(f"[Instrumentation: {', '.join(self.instruments)}]")
        
        # --- Add genre-specific tags ---
        if "Trance" in self.genre:
            style_tags.extend(["[Uplifting]", "[Euphoric]", "[Pluck Lead]", "[Rolling Bassline]", "[Progressive Trance]", "[Trance Build]"])
        elif "Hardcore" in self.genre or "Gabber" in self.genre:
            style_tags.extend(["[Distorted Kick]", "[High-Energy]", "[Aggressive Synth]", "[Industrial Elements]", "[Dark Atmosphere]", "[High-Speed]"])
        elif "Hardstyle" in self.genre:
            style_tags.extend(["[Hardstyle Kick]", "[Reverse Bass]", "[Screeching Synth Lead]", "[Euphoric Melody]", "[High-Energy]"])
        elif "Gabberdisco" in self.genre:
            style_tags.extend(["[Uptempo Disco Beat]", "[Funky Bassline]", "[Distorted Gabber Kick]", "[Catchy Vocal Samples]", "[High-Energy]"])
        elif "House" in self.genre:
            style_tags.extend(["[Four-on-the-floor]", "[Groovy Bassline]", "[Piano Chords]", "[Progressive House]", "[Club Mix]", "[Soulful Vocals]", "[Classic House Piano]", "[Funky Guitar Riffs]"])
        elif "Drum & Bass" in self.genre:
            style_tags.extend(["[Breakbeat]", "[Deep Sub-bass]", "[Reese Bass]"])
        elif "Hard Techno" in self.genre:
            style_tags.extend(["[Driving Rhythm]", "[Hypnotic Sequence]", "[Industrial Kick]", "[Warehouse Rave]", "[Hypnotic Acid Line]", "[Hard Techno]"])
        elif "Techno" in self.genre:
            style_tags.extend(["[Driving Rhythm]", "[Hypnotic Sequence]", "[Industrial Elements]"])
            
        style_prompt = " ".join(style_tags)
        
        # 2. Generate the new structured lyrics template
        lyrics_prompt = self._generate_structured_lyrics_template()
        return {"style_prompt": style_prompt, "lyrics_prompt": lyrics_prompt}


    def generate_thematic(self):
        """Generates a prompt based on a theme or scene."""
        themes = [
            f"A soundtrack for a late-night drive through a neon-lit city, {self.genre}",
            f"Music for a futuristic sci-fi movie scene, epic and {self.mood.lower()}",
            f"An anthem for a massive festival, {self.features['energy']} and euphoric",
            f"The feeling of watching a sunrise over the ocean, calm and serene {self.genre}",
            f"A dark, underground club scene, hypnotic and driving {self.genre}"
        ]
        return random.choice(themes)

    def generate_artist_style(self):
        """Generates a prompt in the style of a famous artist."""
        if self.genre in self.artist_map:
            artist = random.choice(self.artist_map[self.genre])
            return f"{self.genre} in the style of {artist}, {self.mood.lower()}, {self.features['energy']} energy"
        return None # Return None if no artists are defined for the genre

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
        tempo = self.features['tempo']
        tempo_prompt = f"{self.genre}, {int(tempo)} bpm, {self.features['energy']} energy"
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

        # Variation 7: Advanced Mode
        advanced_prompts = self.generate_advanced_mode()
        variations.append({
            "name": "Advanced Mode",
            "prompt": advanced_prompts # This will be a dictionary
        })
        
        return variations
