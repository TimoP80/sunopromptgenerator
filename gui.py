import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
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
from suno_client import SunoClient
from gui_builder import BuildGUI
import subprocess
import config

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

class AccountManager(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("Manage Suno Accounts")
        self.geometry("500x400")
        self.transient(master)
        self.grab_set()

        self.accounts = self.app.load_accounts()
        self.selected_account = tk.StringVar(value=self.app.get_default_account_name())

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Account List ---
        list_frame = ttk.LabelFrame(main_frame, text="Accounts", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.account_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        for name in self.accounts.keys():
            self.account_listbox.insert(tk.END, name)
        self.account_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.account_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.account_listbox.config(yscrollcommand=scrollbar.set)

        # --- Actions ---
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X)

        ttk.Button(actions_frame, text="Add Account...", command=self.add_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="Remove Selected", command=self.remove_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(actions_frame, text="Set as Default", command=self.set_default).pack(side=tk.LEFT)

        # --- Close Button ---
        close_button = ttk.Button(main_frame, text="Close", command=self.destroy)
        close_button.pack(side=tk.BOTTOM, pady=(10, 0))

    def add_account(self):
        dialog = AccountDialog(self, title="Add New Account")
        if dialog.result:
            name, api_key = dialog.result
            if name and api_key:
                self.accounts[name] = {"api_key": api_key}
                self.app.save_accounts(self.accounts)
                self.refresh_list()
                if len(self.accounts) == 1: # If it's the first account, make it default
                    self.app.set_default_account(name)

    def remove_account(self):
        selected_indices = self.account_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select an account to remove.")
            return
        
        account_name = self.account_listbox.get(selected_indices[0])
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to remove '{account_name}'?"):
            del self.accounts[account_name]
            self.app.save_accounts(self.accounts)
            self.refresh_list()
            
            # If the deleted account was the default, clear the default
            if self.app.get_default_account_name() == account_name:
                self.app.set_default_account(None)

    def set_default(self):
        selected_indices = self.account_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select an account to set as default.")
            return
            
        account_name = self.account_listbox.get(selected_indices[0])
        self.app.set_default_account(account_name)
        messagebox.showinfo("Success", f"'{account_name}' has been set as the default account.")

    def refresh_list(self):
        self.account_listbox.delete(0, tk.END)
        for name in self.accounts.keys():
            self.account_listbox.insert(tk.END, name)

class AccountDialog(tk.Toplevel):
    def __init__(self, parent, title=None):
        super().__init__(parent)
        self.transient(parent)
        if title:
            self.title(title)
        
        self.parent = parent
        self.result = None
        
        body = ttk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)
        
        self.buttonbox()
        
        self.grab_set()
        
        if not self.initial_focus:
            self.initial_focus = self
            
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry(f"+{parent.winfo_rootx()+50}+{parent.winfo_rooty()+50}")
        self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self, master):
        ttk.Label(master, text="Account Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(master, text="API Key:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.name_entry = ttk.Entry(master, width=50)
        self.api_key_entry = ttk.Entry(master, width=50)
        
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.api_key_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        master.columnconfigure(1, weight=1)
        
        return self.name_entry


    def buttonbox(self):
        box = ttk.Frame(self)
        
        w = ttk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        
        box.pack()

    def ok(self, event=None):
        self.result = (self.name_entry.get(), self.api_key_entry.get())
        self.destroy()

    def cancel(self, event=None):
        self.destroy()

class AudioPlayer(ttk.Frame):
    def __init__(self, master, result_data, audio_data, task_id, app, **kwargs):
        super().__init__(master, **kwargs)
        self.result_data = result_data
        self.audio_data = audio_data
        self.task_id = task_id # This might be a list of clip_ids now
        self.app = app
        self.playing = False

        self.title = self.result_data.get('title', 'Untitled Track')
        self.audio_url = self.result_data.get('audio_url')
        self.audio_id = self.result_data.get('id') # This is now the clip_id

        self.columnconfigure(1, weight=1)

        # --- Player Controls ---
        controls_frame = ttk.Frame(self, style="Card.TFrame")
        controls_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        controls_frame.columnconfigure(1, weight=1)

        self.play_button = ttk.Button(controls_frame, text="▶ Play", command=self.toggle_play_pause)
        self.play_button.grid(row=0, column=0, padx=(0, 5))

        info_label = ttk.Label(controls_frame, text=self.title, anchor="w", style="Player.TLabel")
        info_label.grid(row=0, column=1, sticky="ew")

        # --- Action Buttons ---
        actions_frame = ttk.Frame(self, style="Card.TFrame")
        actions_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.wav_button = ttk.Button(actions_frame, text="Convert to WAV", command=self.convert_to_wav)
        self.wav_button.pack(side=tk.LEFT, padx=(0, 5))

        self.download_button = ttk.Button(actions_frame, text="Download MP3", command=self.download_mp3)
        self.download_button.pack(side=tk.LEFT)

    def load_audio(self):
        if self.audio_data:
            try:
                # If raw audio data is provided, load it from a BytesIO object
                pygame.mixer.music.load(io.BytesIO(self.audio_data))
                return True
            except pygame.error as e:
                self.app.log(f"Error loading audio from data: {e}")
                return False
        elif self.audio_url:
            # This should already be handled by the main app, but as a fallback
            self.app.log("Audio data not pre-loaded, attempting download...")
            try:
                client = self.app.suno_client
                if not client:
                    self.app.log("Suno client not available for fallback download.")
                    return False
                self.audio_data = client.download_audio(self.audio_url)
                pygame.mixer.music.load(io.BytesIO(self.audio_data))
                return True
            except Exception as e:
                self.app.log(f"Error downloading/loading audio: {e}")
                return False
        else:
            self.app.log("No audio source provided.")
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


    def convert_to_wav(self):
        # This functionality is not supported by the unofficial API
        messagebox.showinfo("Not Supported", "WAV conversion is not available with the current API.")

    def download_mp3(self):
        if not self.audio_data:
            self.app.log("ERROR: Audio data not available for download.")
            messagebox.showerror("Error", "Audio data has not been loaded yet. Please play the track first.")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3")],
            title="Save MP3 File",
            initialfile=f"{self.title}.mp3"
        )
        if save_path:
            try:
                with open(save_path, 'wb') as f:
                    f.write(self.audio_data)
                self.app.log(f"Successfully saved MP3 to: {save_path}")
                messagebox.showinfo("Success", f"File saved to:\n{save_path}")
            except IOError as e:
                self.app.log(f"ERROR: Failed to save MP3 file: {e}")
                messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

class PromptGeneratorGUI:
    def __init__(self, master):
        self.master = master
        master.title("AI Music Studio")
        master.geometry("800x850")
        master.configure(bg="#282c34")

        self.filepath = None
        self.model_cache = {}
        self.analysis_results = {}
        self.genre_rules = self.load_genre_rules()
        self.suno_client = None # Will be initialized after account selection
        
        # --- Initialize Pygame Mixer ---
        pygame.init()
        pygame.mixer.init()

        self.setup_styles()
        self.detect_hardware()
        self.initialize_suno_client()

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

        self.credits_label = ttk.Label(status_frame, text="💰 Suno Credits: N/A")
        self.credits_label.pack(anchor="w")

    def _create_file_selection_ui(self):
        file_frame = ttk.LabelFrame(self.main_frame, text="1. Select Audio File", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_label = ttk.Label(file_frame, text="No file selected.", anchor="w")
        self.file_label.pack(side=tk.LEFT, padx=(5, 10), expand=True, fill=tk.X)

        self.browse_button = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        self.browse_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.import_button = ttk.Button(file_frame, text="Import Analysis...", command=self.import_analysis)
        self.import_button.pack(side=tk.RIGHT, padx=(5, 0))

    def _create_options_ui(self):
        options_frame = ttk.LabelFrame(self.main_frame, text="2. Set Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(options_frame, text="Genre:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.genre_var = tk.StringVar()
        genres = ["Auto-detect"] + sorted([rule['genre'] for rule in self.genre_rules])
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

        self.analyze_button = ttk.Button(action_frame, text="Generate Prompts from Audio", command=self.start_analysis_thread, style="Accent.TButton")
        self.analyze_button.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=5, padx=(0, 5))

        self.instrumental_button = ttk.Button(action_frame, text="Generate Instrumental Music", command=self.start_instrumental_generation_thread, style="Accent.TButton")
        self.instrumental_button.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=5, padx=(5, 0))

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

    def start_instrumental_generation_thread(self):
        self.notebook.select(self.generations_tab)
        
        genre = self.genre_var.get()
        if genre == "Auto-detect":
            genre = "epic cinematic"
            self.log("No genre selected, using 'epic cinematic' as default for instrumental generation.")

        prompt_name = f"Instrumental ({genre})"
        self.log(f"Starting Suno generation for '{prompt_name}'...")
        
        prompt_data = {
            'name': prompt_name,
            'prompt': '',
            'instrumental': True
        }
        
        generation_card = self.add_generation_card(prompt_data['name'], "Queued")
        
        thread = threading.Thread(target=self.run_suno_generation, args=(prompt_data, generation_card), daemon=True)
        thread.start()

    def run_suno_generation(self, prompt_data, generation_card):
        # This runs in a background thread
        status_label = generation_card.status_label
        try:
            if not self.suno_client:
                raise Exception("Suno client not initialized. Please add an account.")

            prompt = prompt_data.get('prompt', '')
            is_custom = prompt_data.get('name', '') == "Advanced Mode"
            is_instrumental = prompt_data.get('instrumental', False)

            # --- Thread-safe UI access ---
            payload_queue = queue.Queue()
            def get_payload_from_ui():
                title = generation_card.title_entry.get()
                tags = generation_card.tags_entry.get()
                
                payload = {
                    'prompt': prompt.get('lyrics_prompt', '') if is_custom else prompt,
                    'is_custom': is_custom,
                    'instrumental': is_instrumental,
                    'title': title,
                    'tags': tags,
                }

                if is_instrumental:
                    payload['prompt'] = ''
                    genre_tag = self.genre_var.get()
                    if genre_tag == "Auto-detect":
                        genre_tag = "epic cinematic"
                    payload['tags'] = genre_tag
                
                payload_queue.put(payload)

            self.master.after(0, get_payload_from_ui)
            payload = payload_queue.get() # This will block until the main thread puts the payload in the queue
            # --- End of thread-safe UI access ---

            # The v1 API returns a list of generation objects
            response_clips = self.suno_client.generate_music(payload)
            generation_ids = [clip['id'] for clip in response_clips if 'id' in clip]
            
            if not generation_ids:
                raise Exception("Failed to get generation IDs from Suno API.")

            self.log(f"Suno request started with generation IDs: {generation_ids}")
            self.poll_suno_status(generation_ids, prompt_data['name'], generation_card)

        except Exception as e:
            error_message = f"ERROR during Suno generation: {e}"
            self.log(error_message)
            self.master.after(0, lambda: status_label.config(text=error_message))

    def poll_suno_status(self, request_ids, prompt_name, generation_card):
        # This runs in a background thread
        import time
        status_label = generation_card.status_label
        progress_var = generation_card.progress_var

        while True:
            try:
                # Network call is safe in a background thread
                response = self.suno_client.check_generation_status(request_ids)
                status = response.get('status', 'unknown')
                
                completed_tracks = len(response.get('results', []))
                total_tracks = len(request_ids)
                progress = (completed_tracks / total_tracks) * 100 if total_tracks > 0 else 0
                
                status_text = f"Status: {status.title()} ({completed_tracks}/{total_tracks} complete)"

                # Schedule UI updates on the main thread
                def update_ui(s, p):
                    status_label.config(text=s)
                    progress_var.set(p)
                self.master.after(0, lambda s=status_text, p=progress: update_ui(s, p))

                if status == 'completed':
                    self.log(f"Suno generation '{prompt_name}' completed.")
                    results = response.get('results', [])
                    # The task_id is now the list of clip_ids
                    self.master.after(0, lambda r=results, c=generation_card, t=request_ids: self.display_suno_results(r, c, t))
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
        
        # --- Title and Tags Entry ---
        input_frame = ttk.Frame(card, style="Card.TFrame")
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Title:").grid(row=0, column=0, padx=(0, 5), sticky="w")
        card.title_entry = ttk.Entry(input_frame)
        card.title_entry.insert(0, f"AI Music - {prompt_name}")
        card.title_entry.grid(row=0, column=1, sticky="ew")
        
        ttk.Label(input_frame, text="Tags:").grid(row=1, column=0, padx=(0, 5), sticky="w")
        card.tags_entry = ttk.Entry(input_frame)
        card.tags_entry.insert(0, self.genre_var.get() if self.genre_var.get() != "Auto-detect" else "")
        card.tags_entry.grid(row=1, column=1, sticky="ew")
        
        input_frame.columnconfigure(1, weight=1)

        # --- Progress and Status ---
        progress_frame = ttk.Frame(card, style="Card.TFrame")
        progress_frame.pack(fill=tk.X, pady=(5, 0))
        progress_frame.columnconfigure(1, weight=1)

        card.status_label = ttk.Label(progress_frame, text=f"Status: {initial_status}")
        card.status_label.grid(row=0, column=0, sticky="w")

        card.progress_var = tk.DoubleVar()
        card.progress_bar = ttk.Progressbar(progress_frame, variable=card.progress_var, maximum=100)
        card.progress_bar.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        return card

    def display_suno_results(self, results, card, task_id):
        # This must be called from the main thread
        for widget in card.winfo_children():
            if "Status:" in widget.cget("text") or "Generating:" in widget.cget("text"):
                widget.pack_forget()
        
        # Add a title to the card based on the first track
        if results:
            card_title = results[0].get('title', 'Generated Tracks')
            ttk.Label(card, text=card_title, font=("Segoe UI", 10, "bold")).pack(anchor="w")

        for i, result in enumerate(results):
            if result.get('audio_url'):
                # This is a network call, so it should be in a thread
                def fetch_and_play(result_data, task_id):
                    try:
                        audio_url = result_data.get('audio_url')
                        self.log(f"Downloading audio for '{result_data.get('title')}'...")
                        audio_data = self.suno_client.download_audio(audio_url)
                        # Switch back to the main thread to create the player
                        self.master.after(0, lambda: self._create_player(card, result_data, audio_data, task_id))
                    except Exception as e:
                        self.log(f"Error fetching audio for {result_data.get('title')}: {e}")

                threading.Thread(target=fetch_and_play, args=(result, task_id), daemon=True).start()
            else:
                self.log(f"No audio_url found for result: {result}")

    def _create_player(self, parent, result_data, audio_data, task_id):
        """Helper to create AudioPlayer on the main thread."""
        player = AudioPlayer(parent, result_data=result_data, audio_data=audio_data, task_id=task_id, app=self, style="Card.TFrame")
        player.pack(fill=tk.X, pady=5)

    def _create_menubar(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import Analysis...", command=self.import_analysis)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

        suno_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Suno", menu=suno_menu)
        suno_menu.add_command(label="Check Credits...", command=self.check_suno_credits)
        suno_menu.add_command(label="Manage Accounts...", command=self.open_account_manager)

        # --- Settings Menu ---
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Edit Genre Rules...", command=self.edit_genre_rules)

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

    def open_account_manager(self):
        AccountManager(self.master, self)

    def check_suno_credits(self, show_messagebox=False):
        """Starts a thread to check Suno API credits and updates the GUI."""
        if not self.suno_client:
            if show_messagebox:
                messagebox.showerror("Error", "Suno client not initialized. Please add an account.")
            return
        
        self.credits_label.config(text="💰 Suno Credits: Loading...")
        threading.Thread(target=self._run_check_credits_worker, args=(show_messagebox,), daemon=True).start()

    def _run_check_credits_worker(self, show_messagebox):
        """Worker thread for fetching credits."""
        try:
            credits_info = self.suno_client.get_credits()
            credits = credits_info.get("credits", "N/A")
            
            def update_gui():
                self.credits_label.config(text=f"💰 Suno Credits: {credits}")
                if show_messagebox:
                    messagebox.showinfo("Suno Credits", f"Remaining Credits: {credits}")
            
            self.master.after(0, update_gui)
            self.log(f"Successfully refreshed Suno credits: {credits}")
        except Exception as e:
            error_message = f"ERROR checking credits: {e}"
            self.log(error_message)
            def update_gui_error():
                self.credits_label.config(text="💰 Suno Credits: Error")
                if show_messagebox:
                    messagebox.showerror("Error", error_message)
            self.master.after(0, update_gui_error)

    def auto_refresh_credits(self):
        """Periodically fetches credits every 30 seconds."""
        self.check_suno_credits(show_messagebox=False)
        self.master.after(30000, self.auto_refresh_credits) # 30 seconds

    def load_genre_rules(self):
        """Loads genre rules from an external JSON file."""
        try:
            with open("genre_rules.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.log(f"ERROR: Could not load genre_rules.json: {e}")
            messagebox.showerror("Error", "Could not load or parse genre_rules.json. Please ensure it exists and is valid.")
            return []

    def edit_genre_rules(self):
        """Opens the genre_rules.json file in the default text editor."""
        try:
            os.startfile("genre_rules.json")
            self.log("Opened genre_rules.json for editing. Please restart the application to apply changes.")
        except Exception as e:
            self.log(f"ERROR: Could not open genre_rules.json: {e}")
            messagebox.showerror("Error", f"Could not open genre_rules.json: {e}")

    def import_analysis(self):
        """Imports a JSON analysis file and generates prompts."""
        filepath = filedialog.askopenfilename(
            title="Select an Analysis JSON File",
            filetypes=(("JSON Files", "*.json"), ("All files", "*.*"))
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r') as f:
                analysis_data = json.load(f)
            
            # --- Validate the imported data ---
            required_keys = ['genre', 'mood', 'instruments', 'has_vocals', 'full_analysis_data']
            if not all(key in analysis_data for key in required_keys):
                raise ValueError("Invalid analysis file. Missing one or more required keys.")

            self.log(f"Successfully imported analysis from: {os.path.basename(filepath)}")
            
            # --- Generate prompts from the imported data ---
            generator = PromptGenerator(
                features=analysis_data['full_analysis_data'],
                genre=analysis_data['genre'],
                mood=analysis_data['mood'],
                instruments=analysis_data['instruments'],
                has_vocals=analysis_data['has_vocals'],
                lyrics=analysis_data.get('lyrics'),
                vocal_gender=analysis_data.get('vocal_gender')
            )
            variations = generator.generate_variations()
            
            # --- Display the results ---
            for tab in [self.prompts_tab, self.analysis_tab]:
                tab.delete(1.0, tk.END)

            self.display_results(variations, analysis_data)
            self.update_progress(100, "Prompts generated from imported data.")
            self.master.after(1500, lambda: self.update_progress(0))

        except (json.JSONDecodeError, ValueError) as e:
            self.log(f"ERROR: Could not import analysis file: {e}")
            messagebox.showerror("Import Error", f"Could not import or parse the analysis file:\n{e}")
        except Exception as e:
            self.log(f"ERROR: An unexpected error occurred during import: {e}")
            messagebox.showerror("Import Error", f"An unexpected error occurred: {e}")


    def on_closing(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        self.master.destroy()

    def load_accounts(self):
        try:
            with open("suno_accounts.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_accounts(self, accounts):
        with open("suno_accounts.json", "w") as f:
            json.dump(accounts, f, indent=4)

    def get_default_account_name(self):
        accounts = self.load_accounts()
        for name, data in accounts.items():
            if data.get('default'):
                return name
        # If no default, return the first account name or None
        return next(iter(accounts), None)

    def set_default_account(self, name):
        accounts = self.load_accounts()
        for acc_name, data in accounts.items():
            data['default'] = (acc_name == name)
        self.save_accounts(accounts)
        self.initialize_suno_client() # Re-initialize with the new default

    def initialize_suno_client(self):
        account_name = self.get_default_account_name()
        if account_name:
            accounts = self.load_accounts()
            api_key = accounts[account_name].get('api_key')
            if api_key:
                self.suno_client = SunoClient(api_key=api_key, base_url=config.SUNO_API_URL)
                self.log(f"Suno client initialized with account: {account_name}")
                # Start the auto-refresh cycle
                self.master.after(1000, self.auto_refresh_credits)
            else:
                self.log(f"ERROR: No API key found for default account '{account_name}'.")
                self.suno_client = None
                self.credits_label.config(text="💰 Suno Credits: N/A")
        else:
            self.log("Suno client not initialized. No default account configured.")
            self.suno_client = None
            self.credits_label.config(text="💰 Suno Credits: N/A")
            # If no accounts exist at all, prompt for creation.
            if not self.load_accounts():
                self.master.after(100, self.prompt_for_account_creation)
            # Otherwise, accounts exist but no default is set, so show a warning.
            else:
                messagebox.showwarning(
                    "Default Account Not Set",
                    "No default Suno account is configured. Please set a default account from the 'Suno > Manage Accounts' menu to enable music generation and credit checking."
                )

    def prompt_for_account_creation(self):
        if messagebox.askyesno("No Suno Account Found", "No Suno account configured. Would you like to add one now?"):
            self.open_account_manager()


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
