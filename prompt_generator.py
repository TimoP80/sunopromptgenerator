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
        
    def generate(self):
        """Generate a Suno v5 compatible prompt"""
        prompt_parts = []
        
        # Add genre
        prompt_parts.append(self.genre)
        
        # Add mood/atmosphere
        prompt_parts.append(self.mood.lower())
        
        # Add tempo descriptor
        tempo = self.features['tempo']
        if tempo > 170:
            prompt_parts.append("hyper-speed")
        elif tempo > 150:
            prompt_parts.append("fast-paced")
        elif tempo > 130:
            prompt_parts.append("up-tempo")
        elif tempo > 110:
            prompt_parts.append("moderate tempo")
        elif tempo > 90:
            prompt_parts.append("mid-tempo")
        elif tempo > 70:
            prompt_parts.append("slow-groove")
        else:
            prompt_parts.append("ballad tempo")
        
        # Add BPM if specific
        if tempo > 100:
            prompt_parts.append(f"{int(tempo)} bpm")
        
        # Add energy descriptor
        energy = self.features['energy']
        if energy == "high":
            prompt_parts.append("high-energy")
        elif energy == "medium":
            prompt_parts.append("driving")
        else: # low
            prompt_parts.append("mellow")
        
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
        prompt = ", ".join(prompt_parts)
        
        return prompt
    
    def generate_detailed(self):
        """Generate a more detailed prompt with additional descriptors"""
        base_prompt = self.generate()
        
        # Add style descriptors based on features
        style_descriptors = []
        
        # Spectral characteristics
        spectral_centroid = self.features['spectral_centroid']
        if spectral_centroid > 3000:
            style_descriptors.append("bright")
        elif spectral_centroid < 1500:
            style_descriptors.append("warm")
        
        # Zero crossing rate (texture)
        zcr = self.features['zero_crossing_rate']
        if zcr > 0.1:
            style_descriptors.append("crisp")
        elif zcr < 0.05:
            style_descriptors.append("smooth")
        
        if style_descriptors:
            return f"{base_prompt}, {', '.join(style_descriptors)}"
        
        return base_prompt
    
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
            "[TITLE: Your Song Title Here]",
            "[ARTIST STYLE: like ...]",
            f"[Genre: {self.genre}]",
            f"[Mood: {self.mood}]",
            "[Era: 2020s]",
            f"[Energy: {self.features['energy']}]",
            f"[BPM: {int(self.features['tempo'])}]",
            f"[Key: {key} {key_mode}]",
        ]
        if self.has_vocals:
            vocal_style = "Ethereal"
            if self.vocal_gender:
                metadata.append(f"[Vocal Style: {vocal_style} {self.vocal_gender} Lead]")
            else:
                metadata.append(f"[Vocal Style: {vocal_style} Lead Vocals]")
            metadata.append("[Vocal Effect: Reverb + Delay]")
        if self.instruments:
            metadata.append(f"[Instrumentation: {', '.join(self.instruments)}]")
        
        metadata.append("[Production: Wide Stereo, Clean Master]")

        # --- 2. Structure Block (Genre-dependent and longer) ---
        is_electronic = "Trance" in self.genre or "EDM" in self.genre or "Hardcore" in self.genre or "Electronic" in self.genre
        
        # Use actual lyrics if available, otherwise use placeholders
        lyrics_placeholder = "Your lyrics here..."
        verse_1_lyrics = self.lyrics if self.lyrics else lyrics_placeholder
        chorus_lyrics = "(Chorus lyrics from above)" if self.lyrics else lyrics_placeholder
        
        structure = []
        if is_electronic:
            metadata.append("[Structure: Extended DJ Mix]")
            structure = [
                "\n[INTRO – 0:00–0:45]",
                "[Instrumental Only]",
                "Atmospheric pads and soft arpeggios. Rolling kick drum builds the groove.",
                "\n[BUILDUP 1 – 0:45–1:30]",
                "Main synth lead teases the melody. Filter sweeps and risers build tension.",
                "\n[VERSE 1 – 1:30–2:15]" if self.has_vocals else "",
                verse_1_lyrics if self.has_vocals else "",
                "\n[BREAKDOWN – 2:15–3:00]",
                "Pads open up, melody emerges. Ethereal textures.",
                "\n[BUILDUP 2 – 3:00–3:45]",
                "Snare roll tension, risers, white noise swell.",
                "\n[DROP / CHORUS – 3:45–4:30]",
                chorus_lyrics if self.has_vocals else "(Big lead melody, full beat, hands-in-the-air moment)",
                "\n[MIDSECTION – 4:30–5:15]",
                "[Instrumental Only]",
                "Main riff continues, evolving filter automation.",
                "\n[OUTRO – 5:15–6:00]",
                "(Instrumental fade-out)",
                "Pads and bassline slowly filter down."
            ]
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
                "Your second verse lyrics here...",
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
            style_tags.extend(["[Uplifting]", "[Euphoric]", "[Pluck Lead]", "[Rolling Bassline]"])
        elif "Hardcore" in self.genre:
            style_tags.extend(["[Distorted Kick]", "[High-Energy]", "[Aggressive Synth]"])
        elif "House" in self.genre:
            style_tags.extend(["[Four-on-the-floor]", "[Groovy Bassline]", "[Piano Chords]"])
        elif "Drum & Bass" in self.genre:
            style_tags.extend(["[Breakbeat]", "[Deep Sub-bass]", "[Reese Bass]"])
            
        style_prompt = " ".join(style_tags)
        
        # 2. Generate the new structured lyrics template
        lyrics_prompt = self._generate_structured_lyrics_template()
        return {"style_prompt": style_prompt, "lyrics_prompt": lyrics_prompt}


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
        
        # Variation 5: Advanced Mode
        advanced_prompts = self.generate_advanced_mode()
        variations.append({
            "name": "Advanced Mode",
            "prompt": advanced_prompts # This will be a dictionary
        })
        
        return variations
