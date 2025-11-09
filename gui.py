import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import multiprocessing
import queue
import os
import json
import torch
import cpuinfo
import pygame
import requests
import io
from audio_analyzer import AudioAnalyzer
from prompt_generator import PromptGenerator
from genre_rules import GENRE_RULES
from suno_client import SunoClient
from gui_builder import BuildGUI

import sys

# --- Analysis Worker Function (for multiprocessing) ---
def run_analysis_in_process(q, filepath, device, genre_var, model_quality_var, demucs_model_var, save_vocals_var):
    """
    This function runs in a separate process to avoid blocking the GUI.
    It communicates with the main thread via a multiprocessing.Queue.
    """
    def _put_in_queue(data):
        try:
            q.put(data)
        except Exception as e:
            # Handle cases where the queue might be closed or full
            print(f"Could not put message in queue: {e}")

    try:
        _put_in_queue({'type': 'progress', 'value': 5, 'log_message': "Analyzing audio features..."})
        # Note: model_cache is not shared across processes. Each process will have its own cache.
        analyzer = AudioAnalyzer(filepath, device=device, model_cache={})
        features = analyzer.analyze()
        
        _put_in_queue({'type': 'progress', 'value': 20, 'log_message': "Detecting tempo and key..."})
        selected_genre = genre_var
        if selected_genre == "Auto-detect":
            selected_genre = None
        
        _put_in_queue({'type': 'progress', 'value': 25, 'log_message': "Classifying genre and mood..."})
        genre = analyzer.classify_genre(selected_genre=selected_genre)
        mood = analyzer.classify_mood()
        
        _put_in_queue({'type': 'progress', 'value': 30, 'log_message': "Analyzing instruments..."})
        instruments = analyzer.detect_instruments(genre)
        has_vocals = analyzer.detect_vocals()
        
        lyrics, vocal_gender = None, None
        if has_vocals:
            _put_in_queue({'type': 'progress', 'value': 40, 'log_message': "Separating vocals (can be slow)..."})
            model_quality = model_quality_var
            demucs_model = demucs_model_var
            save_vocals = save_vocals_var
            
            _put_in_queue({'type': 'progress', 'value': 60, 'log_message': f"Transcribing lyrics with Whisper ({model_quality})..."})
            vocal_info = analyzer.extract_lyrics(
                model_quality=model_quality,
                demucs_model=demucs_model,
                save_vocals=save_vocals,
                output_dir=os.path.dirname(filepath)
            )
            lyrics = vocal_info.get('lyrics')
            vocal_gender = vocal_info.get('gender')
        
        _put_in_queue({'type': 'progress', 'value': 90, 'log_message': "Generating prompts..."})
        generator = PromptGenerator(features, genre, mood, instruments, has_vocals, lyrics, vocal_gender)
        variations = generator.generate_variations()
        
        result_data = {
            'type': 'result',
            'prompts': variations,
            'analysis_data': {
                'genre': genre, 'mood': mood, 'instruments': instruments,
                'has_vocals': has_vocals, 'lyrics': lyrics, 'vocal_gender': vocal_gender,
                'full_analysis_data': features
            }
        }
        _put_in_queue(result_data)

    except Exception as e:
        import traceback
        _put_in_queue({'type': 'error', 'error': str(e), 'traceback': traceback.format_exc()})
    finally:
        _put_in_queue({'type': 'done'})

class AudioPlayer(ttk.Frame):
    def __init__(self, master, title, audio_url=None, audio_data=None, **kwargs):
        super().__init__(master, **kwargs)
        self.audio_url = audio_url
        self.title = title
        self.audio_data = audio_data
        self.playing = False

        self.columnconfigure(1, weight=1)

        self.play_button = ttk.Button(self, text="▶ Play", command=self.toggle_play_pause)
        self.play_button.grid(row=0, column=0, padx=(0, 5))

        info_label = ttk.Label(self, text=self.title, anchor="w", style="Player.TLabel")
        info_label.grid(row=0, column=1, sticky="ew")

    def load_audio(self):
        if self.audio_data:
            try:
                # If raw audio data is provided, load it from a BytesIO object
                pygame.mixer.music.load(io.BytesIO(self.audio_data))
                return True
            except pygame.error as e:
                print(f"Error loading audio from data: {e}")
                return False
        elif self.audio_url:
            try:
                # Fallback to loading from URL
                response = requests.get(self.audio_url, stream=True)
                response.raise_for_status()
                self.audio_data = response.content  # Store the content
                pygame.mixer.music.load(io.BytesIO(self.audio_data))
                return True
            except requests.exceptions.RequestException as e:
                print(f"Error downloading audio: {e}")
                return False
        else:
            print("No audio source provided.")
            return False

    def toggle_play_pause(self):
        if not self.playing:
            if self.load_audio():
                pygame.mixer.music.play()
                self.play_button.config(text="❚❚ Pause")
                self.playing = True
        else:
            pygame.mixer.music.pause()
            self.play_button.config(text="▶ Play")
            self.playing = False

class PromptGeneratorGUI:
    def __init__(self, master):
        self.master = master
        master.title("AI Music Studio")
        master.geometry("800x850")
        master.configure(bg="#282c34")

        self.filepath = None
        self.model_cache = {}
        self.analysis_results = {}
        
        # --- Initialize Pygame Mixer ---
        pygame.init()
        pygame.mixer.init()

        self.setup_styles()
        self.detect_hardware()

        self._create_menubar()
        
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Header ---
        header_frame = tk.Frame(master, bg="#282c34")
        header_frame.pack(pady=(20, 10), fill=tk.X)
        
        title_label = tk.Label(header_frame, text="🎶 AI Music Studio 🎶", font=("Segoe UI", 20, "bold"), fg="#e6e6e6", bg="#282c34")
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="v1.5.0 - Analyze Audio, Generate Prompts, and Create Music with AI", font=("Segoe UI", 10), fg="#888888", bg="#282c34")
        subtitle_label.pack(pady=(0, 20))

        # --- Main Frame ---
        self.main_frame = ttk.Frame(master, style="Main.TFrame", padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self._create_status_ui()
        self._create_file_selection_ui()
        self._create_options_ui()
        self._create_action_ui()
        self._create_metadata_ui()
        self._create_results_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # --- Colors ---
        BG_COLOR = "#282c34"
        FG_COLOR = "#abb2bf"
        BORDER_COLOR = "#3e4451"
        SELECT_BG_COLOR = "#3e4451"
        ACCENT_COLOR = "#61afef"
        
        style.configure(".", background=BG_COLOR, foreground=FG_COLOR, bordercolor=BORDER_COLOR, lightcolor=BG_COLOR, darkcolor=BG_COLOR)
        style.configure("Player.TLabel", background="#21252b", foreground=FG_COLOR, font=("Segoe UI", 9))
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Main.TFrame", background="#21252b", borderwidth=1, relief="solid", bordercolor=BORDER_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 9))
        style.configure("TLabelframe", background=BG_COLOR, bordercolor=BORDER_COLOR, font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", foreground=FG_COLOR, background=BG_COLOR)
        
        style.configure("TButton", background=ACCENT_COLOR, foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TButton", background=[('active', '#569cd6')])
        
        style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), padding=(10, 10))

        style.configure("TCombobox", background=SELECT_BG_COLOR, foreground=FG_COLOR, fieldbackground=SELECT_BG_COLOR, bordercolor=BORDER_COLOR)
        style.map("TCombobox", fieldbackground=[('readonly', SELECT_BG_COLOR)])

        style.configure("TProgressbar", troughcolor=BG_COLOR, background=ACCENT_COLOR, bordercolor=BORDER_COLOR)

        # --- Notebook/Tab Styling ---
        style.configure("TNotebook.Tab", foreground="black", padding=(10, 5))
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT_COLOR)],
                  foreground=[("selected", "white")])

    def detect_hardware(self):
        self.cpu_model = cpuinfo.get_cpu_info().get('brand_raw', 'N/A')
        self.pytorch_gpu = torch.cuda.is_available()
        self.gpu_model = "N/A"
        if self.pytorch_gpu:
            self.gpu_model = torch.cuda.get_device_name(0)
        self.device = 'cuda' if self.pytorch_gpu else 'cpu'

    def _create_status_ui(self):
        status_frame = ttk.LabelFrame(self.main_frame, text="System Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(status_frame, text=f"🖥️ CPU: {self.cpu_model}").pack(anchor="w")
        ttk.Label(status_frame, text=f"🎮 GPU: {self.gpu_model}").pack(anchor="w")

        processing_device = "GPU" if self.pytorch_gpu else "CPU"
        status_color = "#98c379" if self.pytorch_gpu else "#e5c07b"

        status_style_name = f"{processing_device}.TLabel"
        style = ttk.Style()
        style.configure(status_style_name, foreground=status_color)

        ttk.Label(status_frame, text=f"AI Processing (Demucs & Whisper): ● {processing_device}", style=status_style_name).pack(anchor="w")

    def _create_file_selection_ui(self):
        file_frame = ttk.LabelFrame(self.main_frame, text="1. Select Audio File", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_label = ttk.Label(file_frame, text="No file selected.", anchor="w")
        self.file_label.pack(side=tk.LEFT, padx=(5, 10), expand=True, fill=tk.X)

        self.browse_button = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        self.browse_button.pack(side=tk.RIGHT, padx=(5, 0))

    def _create_options_ui(self):
        options_frame = ttk.LabelFrame(self.main_frame, text="2. Set Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(options_frame, text="Genre:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.genre_var = tk.StringVar()
        genres = ["Auto-detect"] + sorted([rule['genre'] for rule in GENRE_RULES])
        self.genre_menu = ttk.Combobox(options_frame, textvariable=self.genre_var, values=genres, state="readonly")
        self.genre_menu.set("Auto-detect")
        self.genre_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(options_frame, text="Whisper Model:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.model_quality_var = tk.StringVar(value='base')
        models = [
            'tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en',
            'medium', 'medium.en', 'large'
        ]
        self.model_quality_menu = ttk.Combobox(options_frame, textvariable=self.model_quality_var, values=models, state="readonly")
        self.model_quality_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(options_frame, text="Separation Quality:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.demucs_model_var = tk.StringVar(value='htdemucs_ft')
        demucs_models = ['htdemucs_ft', 'hdemucs_mmi', 'mdx_extra']
        self.demucs_model_menu = ttk.Combobox(options_frame, textvariable=self.demucs_model_var, values=demucs_models, state="readonly")
        self.demucs_model_menu.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.save_vocals_var = tk.BooleanVar(value=False)
        self.save_vocals_check = ttk.Checkbutton(options_frame, text="Save Extracted Vocals", variable=self.save_vocals_var)
        self.save_vocals_check.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.auto_lyrics_var = tk.BooleanVar(value=False)
        self.auto_lyrics_check = ttk.Checkbutton(options_frame, text="Auto-generate Lyrics (Advanced Mode)", variable=self.auto_lyrics_var)
        self.auto_lyrics_check.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        options_frame.columnconfigure(1, weight=1)

    def _create_action_ui(self):
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        self.analyze_button = ttk.Button(action_frame, text="Generate Prompts", command=self.start_analysis_thread, style="Accent.TButton")
        self.analyze_button.pack(fill=tk.X, ipady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(10, 5))

    def _create_metadata_ui(self):
        self.metadata_frame = ttk.LabelFrame(self.main_frame, text="Quick Info", padding=10)
        # Initially hidden, will be shown after file selection
        
        self.metadata_text = tk.Text(self.metadata_frame, height=6, wrap=tk.WORD, bg="#282c34", fg="#abb2bf", relief=tk.FLAT, font=("Segoe UI", 9))
        self.metadata_text.pack(fill=tk.BOTH, expand=True)
        self.metadata_text.bind("<Key>", self._prevent_text_edit)

    def _create_results_ui(self):
        results_frame = ttk.LabelFrame(self.main_frame, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.log_tab = self._create_scrolled_text_tab("Log")
        self.prompts_tab = self._create_scrolled_text_tab("Generated Prompts")
        self.analysis_tab = self._create_scrolled_text_tab("Full Analysis")
        self.generations_tab, self.generations_content_frame = self._create_generations_tab("Music Generations")

    def _create_scrolled_text_tab(self, title):
        tab = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, bg="#282c34", fg="#abb2bf", relief=tk.FLAT)
        self.notebook.add(tab, text=title)
        tab.bind("<Key>", self._prevent_text_edit)
        return tab

    def _create_generations_tab(self, title):
        tab_container = ttk.Frame(self.notebook)
        self.notebook.add(tab_container, text=title)
        
        canvas = tk.Canvas(tab_container, bg="#282c34", highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab_container, orient="vertical", command=canvas.yview)
        content_frame = ttk.Frame(canvas)

        content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return tab_container, content_frame

    def browse_file(self):
        self.filepath = filedialog.askopenfilename(
            title="Select an Audio File",
            filetypes=(("Audio Files", "*.wav *.mp3 *.flac"), ("All files", "*.*"))
        )
        if self.filepath:
            self.file_label.config(text=os.path.basename(self.filepath))
            self.log(f"Selected file: {self.filepath}")
            # Start a thread to extract metadata without blocking the GUI
            threading.Thread(target=self.display_metadata, daemon=True).start()
        else:
            self.file_label.config(text="No file selected.")
            self.metadata_frame.pack_forget()

    def start_analysis_thread(self):
        if not self.filepath:
            self.log("ERROR: Please select a file first.")
            return

        self.analyze_button.config(state=tk.DISABLED)
        self.progress_var.set(0)
        
        for tab in [self.log_tab, self.prompts_tab, self.analysis_tab]:
            tab.delete(1.0, tk.END)
        
        self.log("Starting analysis...")
        self.notebook.select(self.log_tab)

        # --- Use multiprocessing for heavy analysis ---
        self.analysis_queue = multiprocessing.Queue()
        analysis_args = (
            self.analysis_queue,
            self.filepath,
            self.device,
            self.genre_var.get(),
            self.model_quality_var.get(),
            self.demucs_model_var.get(),
            self.save_vocals_var.get()
        )
        
        self.analysis_process = multiprocessing.Process(target=run_analysis_in_process, args=analysis_args)
        self.analysis_process.start()
        
        # Start checking the queue for updates
        self.master.after(100, self.process_analysis_queue)

    def process_analysis_queue(self):
        try:
            message = self.analysis_queue.get_nowait()
            
            msg_type = message.get('type')
            
            if msg_type == 'progress':
                self.update_progress(message['value'], message.get('log_message'))
            elif msg_type == 'log':
                self.log(message['message'])
            elif msg_type == 'result':
                self.display_results(message['prompts'], message['analysis_data'])
                self.update_progress(100, "Analysis complete!")
            elif msg_type == 'error':
                self.log(f"\nERROR: An unexpected error occurred: {message['error']}")
                self.update_progress(0, "Error")
            elif msg_type == 'done':
                self.enable_button()
                if self.device == 'cuda':
                    torch.cuda.empty_cache()
                return # Stop polling
                
        except queue.Empty:
            pass # No message yet, check again later
        finally:
            # Keep checking as long as the process is alive
            if self.analysis_process.is_alive() or not self.analysis_queue.empty():
                self.master.after(100, self.process_analysis_queue)
            else: # Process finished, do final cleanup
                 self.enable_button()

    def update_progress(self, value, log_message=None):
        if log_message:
            self.log(log_message)
        self.master.after(0, lambda: self.progress_var.set(value))

    def log(self, message):
        def callback():
            self.log_tab.insert(tk.END, message + "\n")
            self.log_tab.see(tk.END)
        self.master.after(0, callback)

    def display_results(self, prompts, analysis_data):
        self.analysis_results = analysis_data
        def callback():
            for prompt in prompts:
                if prompt['name'] == "Advanced Mode":
                    self.prompts_tab.insert(tk.END, f"--- {prompt['name']} ---\n")
                    self.prompts_tab.insert(tk.END, f"Style Prompt:\n{prompt['prompt']['style_prompt']}\n\n")
                    self.prompts_tab.insert(tk.END, f"Lyrics Prompt:\n{prompt['prompt']['lyrics_prompt']}\n\n")
                else:
                    self.prompts_tab.insert(tk.END, f"--- {prompt['name']} ---\n{prompt['prompt']}\n\n")
                
                # Add a generate button for each prompt
                generate_button = ttk.Button(
                    self.prompts_tab,
                    text=f"Generate Music from '{prompt['name']}'",
                    command=lambda p=prompt: self.start_suno_generation_thread(p)
                )
                self.prompts_tab.window_create(tk.END, window=generate_button)
                self.prompts_tab.insert(tk.END, "\n\n")

            self.analysis_tab.insert(tk.END, json.dumps(analysis_data, indent=4))
            
            self.notebook.select(self.prompts_tab)

        self.master.after(0, callback)

    def enable_button(self):
        self.analyze_button.config(state=tk.NORMAL)
        self.master.after(1500, lambda: self.update_progress(0))

    def display_metadata(self):
        try:
            analyzer = AudioAnalyzer(self.filepath, device=self.device, model_cache=self.model_cache)
            metadata = analyzer.extract_metadata()
            
            # --- Perform a quick analysis for more detailed info ---
            try:
                if analyzer.y is None:
                    analyzer.load_audio()
                
                quick_analysis = {
                    "Tempo (BPM)": analyzer.get_tempo(),
                    "Key": analyzer.get_key(),
                    "Energy": analyzer.get_energy().title()
                }
                metadata.update(quick_analysis)
            except Exception as e:
                self.log(f"Could not perform quick analysis: {e}")

            # Format metadata for display
            metadata_str = "\n".join([f"{key}: {value}" for key, value in metadata.items()])

            def callback():
                self.metadata_text.delete(1.0, tk.END)
                self.metadata_text.insert(tk.END, metadata_str)
                self.metadata_frame.pack(fill=tk.X, pady=10, before=self.progress_bar)

            self.master.after(0, callback)

        except Exception as e:
            self.log(f"ERROR: Could not extract metadata: {e}")
            self.master.after(0, lambda: self.metadata_frame.pack_forget())

    def start_suno_generation_thread(self, prompt_data):
        self.notebook.select(self.generations_tab)
        self.log(f"Starting Suno generation for '{prompt_data['name']}'...")
        
        # Create UI elements on the main thread before starting the background task
        generation_card = self.add_generation_card(prompt_data['name'], "Queued")
        
        thread = threading.Thread(target=self.run_suno_generation, args=(prompt_data, generation_card), daemon=True)
        thread.start()

    def run_suno_generation(self, prompt_data, generation_card):
        # This runs in a background thread
        status_label = generation_card.winfo_children()[1]
        try:
            client = SunoClient()
            prompt = prompt_data['prompt']
            is_custom = prompt_data['name'] == "Advanced Mode"
            
            # Network call is safe in a background thread
            # Construct the correct payload based on the new API structure
            vocal_gender = self.analysis_results.get('vocal_gender')
            if vocal_gender:
                vocal_gender = vocal_gender[0].lower() # 'm' or 'f'

            kwargs = {
                'title': f"AI Music - {prompt_data['name']}",
                'tags': prompt.get('style_prompt') if is_custom else self.genre_var.get(),
                'make_instrumental': False, # Or get this from the UI if you add an option
                'vocal_gender': vocal_gender,
                'auto_lyrics': self.auto_lyrics_var.get()
            }
            response = client.generate_music(prompt, is_custom=is_custom, **kwargs)
            request_id = response.get('request_id')
            
            if not request_id:
                raise Exception("Failed to get request ID from Suno API.")

            self.log(f"Suno request started with ID: {request_id}")
            self.poll_suno_status(request_id, prompt_data['name'], generation_card)

        except Exception as e:
            error_message = f"ERROR during Suno generation: {e}"
            self.log(error_message)
            # Schedule UI updates on the main thread
            self.master.after(0, lambda: status_label.config(text=error_message))

    def poll_suno_status(self, request_id, prompt_name, generation_card):
        # This runs in a background thread
        import time
        status_label = generation_card.winfo_children()[1]

        while True:
            try:
                client = SunoClient()
                # Network call is safe in a background thread
                response = client.check_generation_status(request_id)
                status = response.get('status', 'unknown')
                
                # Schedule UI updates on the main thread
                self.master.after(0, lambda s=status: status_label.config(text=f"Status: {s}"))

                if status == 'completed':
                    self.log(f"Suno generation '{prompt_name}' completed.")
                    results = response.get('results', [])
                    # Schedule the creation of result widgets on the main thread
                    self.master.after(0, lambda r=results, c=generation_card: self.display_suno_results(r, c))
                    break
                elif status == 'failed':
                    raise Exception(response.get('message', 'Generation failed without a specific message.'))
                
                time.sleep(5) # This is safe in a background thread

            except Exception as e:
                error_message = f"ERROR polling Suno status: {e}"
                self.log(error_message)
                # Schedule UI updates on the main thread
                self.master.after(0, lambda: status_label.config(text=error_message))
                break

    def add_generation_card(self, prompt_name, initial_status):
        card = ttk.Frame(self.generations_content_frame, style="Card.TFrame", padding=10)
        card.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(card, text=f"Generating: {prompt_name}", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(card, text=f"Status: {initial_status}").pack(anchor="w")
        
        return card

    def display_suno_results(self, results, card):
        # This must be called from the main thread
        for widget in card.winfo_children():
            if "Status:" in widget.cget("text"):
                widget.pack_forget()

        client = SunoClient()
        for i, result in enumerate(results):
            clip_id = result.get('clip_id')
            if clip_id:
                try:
                    # This is a network call, so it should be in a thread
                    def fetch_and_play(clip_id, title):
                        try:
                            wav_data = client.get_wav(clip_id)
                            # Switch back to the main thread to create the player
                            self.master.after(0, lambda: self._create_player(card, title, wav_data))
                        except Exception as e:
                            self.log(f"Error fetching WAV for {clip_id}: {e}")

                    title = result.get('title', f"Track {i+1}")
                    threading.Thread(target=fetch_and_play, args=(clip_id, title), daemon=True).start()

                except Exception as e:
                    self.log(f"Error initiating WAV fetch for {clip_id}: {e}")
            else:
                self.log(f"No clip_id found for result: {result}")

    def _create_player(self, parent, title, audio_data):
        """Helper to create AudioPlayer on the main thread."""
        player = AudioPlayer(parent, title=title, audio_data=audio_data, style="Card.TFrame")
        player.pack(fill=tk.X, pady=5)

    def _create_menubar(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.master.quit)

        build_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Build", menu=build_menu)
        build_menu.add_command(label="Build Application...", command=self.open_build_window)

    def open_build_window(self):
        if hasattr(self, 'build_window') and self.build_window.winfo_exists():
            self.build_window.lift()
            return
        
        self.build_window = tk.Toplevel(self.master)
        build_gui = BuildGUI(self.build_window)

    def _prevent_text_edit(self, event):
        # Allow copying text with Ctrl+C, but prevent any other modification
        if event.state == 4 and event.keysym == 'c':
            return
        return "break"

    def on_closing(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        self.master.destroy()

if __name__ == "__main__":
    # --- Splash Screen Handling ---
    is_bundle = hasattr(sys, '_MEIPASS')
    if is_bundle:
        try:
            import pyi_splash
            pyi_splash.update_text("Initializing application...")
        except (ImportError, RuntimeError):
            pass

    multiprocessing.freeze_support()
    root = tk.Tk()
    gui = PromptGeneratorGUI(root)

    # Close the splash screen once the main window is ready
    if is_bundle:
        try:
            import pyi_splash
            pyi_splash.close()
        except (ImportError, RuntimeError):
            pass

    root.mainloop()
