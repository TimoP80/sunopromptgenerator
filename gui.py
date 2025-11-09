import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import os
import json
import torch
import cpuinfo
from audio_analyzer import AudioAnalyzer
from prompt_generator import PromptGenerator
from genre_rules import GENRE_RULES

class PromptGeneratorGUI:
    def __init__(self, master):
        self.master = master
        master.title("Suno Prompt Generator")
        master.geometry("800x850")
        master.configure(bg="#1e1e1e")

        self.filepath = None
        self.model_cache = {}
        self.setup_styles()
        self.detect_hardware()

        # --- Header ---
        header_frame = tk.Frame(master, bg="#1e1e1e")
        header_frame.pack(pady=(20, 10), fill=tk.X)
        
        title_label = tk.Label(header_frame, text="🤖 AI-Powered Suno Prompt Generator", font=("Segoe UI", 20, "bold"), fg="#ffffff", bg="#1e1e1e")
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="Upload any audio file to generate highly detailed prompts for Suno AI", font=("Segoe UI", 10), fg="#a0a0a0", bg="#1e1e1e")
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
        BG_COLOR = "#2a2d30"
        FG_COLOR = "#cccccc"
        BORDER_COLOR = "#404040"
        SELECT_BG_COLOR = "#3a3d40"
        ACCENT_COLOR = "#667eea"

        style.configure(".", background=BG_COLOR, foreground=FG_COLOR, bordercolor=BORDER_COLOR, lightcolor=BG_COLOR, darkcolor=BG_COLOR)
        
        style.configure("TFrame", background=BG_COLOR)
        style.configure("Main.TFrame", background="#3c3f41", borderwidth=1, relief="solid", bordercolor=BORDER_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 9))
        style.configure("TLabelframe", background=BG_COLOR, bordercolor=BORDER_COLOR, font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", foreground=FG_COLOR, background=BG_COLOR)
        
        style.configure("TButton", background=ACCENT_COLOR, foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TButton", background=[('active', '#764ba2')])
        
        style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), padding=(10, 10))

        style.configure("TCombobox", background=SELECT_BG_COLOR, foreground=FG_COLOR, fieldbackground=SELECT_BG_COLOR, bordercolor=BORDER_COLOR)
        style.map("TCombobox", fieldbackground=[('readonly', SELECT_BG_COLOR)])

        style.configure("TProgressbar", troughcolor=BG_COLOR, background=ACCENT_COLOR, bordercolor=BORDER_COLOR)

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
        status_color = "#4caf50" if self.pytorch_gpu else "#f57f17"

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
        
        self.metadata_text = tk.Text(self.metadata_frame, height=6, wrap=tk.WORD, state="disabled", bg="#2a2d30", fg="#cccccc", relief=tk.FLAT, font=("Segoe UI", 9))
        self.metadata_text.pack(fill=tk.BOTH, expand=True)

    def _create_results_ui(self):
        results_frame = ttk.LabelFrame(self.main_frame, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.log_tab = self._create_scrolled_text_tab("Log")
        self.prompts_tab = self._create_scrolled_text_tab("Generated Prompts")
        self.analysis_tab = self._create_scrolled_text_tab("Full Analysis")

    def _create_scrolled_text_tab(self, title):
        tab = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, state="disabled", bg="#2a2d30", fg="#cccccc", relief=tk.FLAT)
        self.notebook.add(tab, text=title)
        return tab

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
            tab.config(state="normal")
            tab.delete(1.0, tk.END)
            tab.config(state="disabled")
        
        self.log("Starting analysis...")
        self.notebook.select(self.log_tab)

        self.thread = threading.Thread(target=self.run_analysis)
        self.thread.daemon = True
        self.thread.start()

    def run_analysis(self):
        try:
            self.update_progress(5, "Analyzing audio features...")
            analyzer = AudioAnalyzer(self.filepath, device=self.device, model_cache=self.model_cache)
            features = analyzer.analyze()
            
            self.update_progress(20, "Classifying genre and mood...")
            selected_genre = self.genre_var.get()
            if selected_genre == "Auto-detect":
                selected_genre = None
            genre = analyzer.classify_genre(selected_genre=selected_genre)
            mood = analyzer.classify_mood()
            instruments = analyzer.detect_instruments()
            has_vocals = analyzer.detect_vocals()
            
            lyrics, vocal_gender = None, None
            if has_vocals:
                self.update_progress(40, "Separating vocals and transcribing lyrics (this can be slow)...")
                model_quality = self.model_quality_var.get()
                vocal_info = analyzer.extract_lyrics(model_quality=model_quality)
                lyrics = vocal_info.get('lyrics')
                vocal_gender = vocal_info.get('gender')
            
            self.update_progress(90, "Generating prompts...")
            generator = PromptGenerator(features, genre, mood, instruments, has_vocals, lyrics, vocal_gender)
            variations = generator.generate_variations()
            
            self.update_progress(100, "Analysis complete!")
            
            self.display_results(variations, {
                'genre': genre, 'mood': mood, 'instruments': instruments, 
                'has_vocals': has_vocals, 'lyrics': lyrics, 'vocal_gender': vocal_gender,
                'full_analysis_data': features
            })

        except Exception as e:
            self.log(f"\nERROR: An unexpected error occurred: {e}")
            self.update_progress(0, "Error")
        finally:
            self.master.after(0, self.enable_button)

    def update_progress(self, value, log_message=None):
        if log_message:
            self.log(log_message)
        self.master.after(0, lambda: self.progress_var.set(value))

    def log(self, message):
        def callback():
            self.log_tab.config(state="normal")
            self.log_tab.insert(tk.END, message + "\n")
            self.log_tab.see(tk.END)
            self.log_tab.config(state="disabled")
        self.master.after(0, callback)

    def display_results(self, prompts, analysis_data):
        def callback():
            self.prompts_tab.config(state="normal")
            for prompt in prompts:
                if prompt['name'] == "Advanced Mode":
                    self.prompts_tab.insert(tk.END, f"--- {prompt['name']} ---\n")
                    self.prompts_tab.insert(tk.END, f"Style Prompt:\n{prompt['prompt']['style_prompt']}\n\n")
                    self.prompts_tab.insert(tk.END, f"Lyrics Prompt:\n{prompt['prompt']['lyrics_prompt']}\n\n")
                else:
                    self.prompts_tab.insert(tk.END, f"--- {prompt['name']} ---\n{prompt['prompt']}\n\n")
            self.prompts_tab.config(state="disabled")

            self.analysis_tab.config(state="normal")
            self.analysis_tab.insert(tk.END, json.dumps(analysis_data, indent=4))
            self.analysis_tab.config(state="disabled")
            
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
                self.metadata_text.config(state="normal")
                self.metadata_text.delete(1.0, tk.END)
                self.metadata_text.insert(tk.END, metadata_str)
                self.metadata_text.config(state="disabled")
                self.metadata_frame.pack(fill=tk.X, pady=10, before=self.progress_bar)

            self.master.after(0, callback)

        except Exception as e:
            self.log(f"ERROR: Could not extract metadata: {e}")
            self.master.after(0, lambda: self.metadata_frame.pack_forget())

if __name__ == "__main__":
    root = tk.Tk()
    gui = PromptGeneratorGUI(root)
    root.mainloop()