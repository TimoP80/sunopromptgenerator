# AI Music Studio

An advanced, AI-driven tool to analyze audio, generate detailed prompts, and create music with the Suno API. Features automated lyric extraction, vocal separation, and GPU acceleration for rapid results.

## Key Features

- **Native Desktop GUI**: A complete, self-contained desktop application built with `tkinter`—no web browser needed.
- **Suno API Integration**: Generate music directly from your prompts within the application.
- **Advanced Audio Analysis**:
  - **Creative Engine**: Employs a sophisticated, rule-based system to generate creative and context-aware prompts.
  - **Detailed Metrics**: Extracts tempo, key, energy, genre, mood, and advanced metrics like spectral contrast and bandwidth.
  - **Accurate Key Detection**: Uses an advanced algorithm to accurately determine both the key and its mode (major/minor).
- **AI-Powered Vocal Processing**:
  - **Vocal Separation**: Isolates vocals from any track using Meta's Demucs model.
  - **Lyrics Transcription**: Transcribes lyrics with OpenAI's Whisper, offering multiple model sizes for a speed/accuracy trade-off.
  - **Save Vocals**: Option to save the isolated vocal track as a separate WAV file.
- **Powerful Prompt Generation**:
  - **Multiple Formats**: Generates prompts in Standard, Creative, and Advanced (custom mode) formats.
  - **Data-Driven Refinement**: The "Refinement Prompt" creates a highly prescriptive, multi-line prompt with exact numerical data for precise iterative control.
  - **Enhanced Lyrics Template**: Generates creative and context-aware lyric structures based on the song's mood and energy.
- **Performance & UX**:
  - **GPU Acceleration**: Automatically uses an NVIDIA GPU (if available) for Demucs and Whisper, with CUDA optimizations for a faster, more stable experience.
  - **Instant Feedback**: A "Quick Info" panel provides immediate analysis results (tempo, key, energy) upon file selection.
  - **Flexible Build System**: Easy-to-use build scripts (`build_gui.bat`, `build_cli.bat`) with options for UPX compression to reduce executable size.

## How It Works

The application uses a sophisticated pipeline to transform an audio file into a set of detailed music generation prompts:

1.  **File Selection**: The user selects an audio file via the native `tkinter` GUI.
2.  **Quick Analysis**: The application immediately runs a lightweight analysis to extract tempo, key, and energy, displaying them in the "Quick Info" panel.
3.  **Full Analysis Pipeline**:
    - **Vocal Separation (`demucs`)**: The audio is processed by Meta's Demucs model to separate it into vocals, drums, bass, and other stems.
    - **Lyrics Transcription (`Whisper`)**: The isolated vocal track is fed into OpenAI's Whisper model to transcribe the lyrics.
    - **Deep Audio Analysis (`librosa`)**: The `AudioAnalyzer` class uses `librosa` to extract a wide range of musical features, including spectral characteristics, tonnetz, and more.
    - **Genre & Mood Classification**: A rule-based engine in `genre_rules.py` classifies the genre and mood from the extracted features.
4.  **Prompt Generation**: The `PromptGenerator` class synthesizes all the analyzed data—lyrics, genre, mood, and detailed metrics—into multiple creative and technical prompts.
5.  **Display Results**: The final analysis and generated prompts are displayed in the GUI, ready to be used.
6.  **Music Generation**: The user can click a "Generate Music" button to send any prompt directly to the Suno API and listen to the result.

## Dependencies

This project relies on several key Python libraries:

-   **Tkinter**: For the native desktop GUI (part of the Python standard library).
-   **Librosa**: A powerful library for audio analysis and feature extraction.
-   **Demucs**: Meta AI's state-of-the-art music source separation model.
-   **Whisper**: OpenAI's robust model for speech-to-text transcription.
-   **Requests**: For communicating with the Suno API.
-   **PyTorch**: The underlying deep learning framework for `demucs` and `Whisper`.
-   **Numpy**: For numerical operations on audio data.

## Building the Executable

This project includes robust scripts to build a standalone executable using PyInstaller, packaging the entire application into a single folder for easy distribution.

### Prerequisites

- **Python 3.12**: Ensure you have Python 3.12 installed and accessible from your command line.
- **Virtual Environment**: It is highly recommended to use a virtual environment to avoid conflicts with other Python projects.

### Build Methods

You can build the application using either the integrated GUI tool or the command-line scripts.

#### Method 1: Building from the GUI (Recommended)

The easiest way to build is by using the integrated build tool.

1.  **Launch the Application**:
    ```bash
    python gui.py
    ```
2.  **Open the Build Tool**: From the main menu, select **Build > Build Application...**.
3.  **Use the Build Tool**:
    - **System Check**: Verifies that PyInstaller and UPX are installed.
    - **Install Dependencies**: Click to install all required packages from `requirements.txt`.
    - **Build Options**: Choose the build target (GUI or CLI) and toggle UPX compression.
    - **Start Build**: Click "Start Build" to begin. After a successful build, use "Open Output Folder" to access the executable.

#### Method 2: Command-Line Build

For users who prefer the command line, dedicated scripts are available.

1.  **Create and Activate Virtual Environment**:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Build Script**:
    - **To build the GUI application (default):**
      ```bash
      build_gui.bat
      ```
    - **To build the command-line application:**
      ```bash
      build_cli.bat
      ```
4.  **Find the Executable**: The application will be in the `dist` folder.

## Usage

1.  Upload an audio file.
2.  Select your desired transcription quality.
3.  Wait for the analysis to complete, watching the real-time progress updates.
4.  Copy the generated prompts from the "Basic", "Detailed", or "Advanced Mode" cards.
5.  For "Advanced Mode", paste the "Style of Music" prompt into the corresponding field in Suno, and the "Lyrics Template" into the lyrics field.
6.  Edit and refine the prompts in Suno to create your music.

## Configuration

The application's settings can be modified in the `config.py` file:

-   `SUNO_API_KEY`: Your API key for the AI Music API. **This must be configured to use the music generation feature.**
-   `UPLOAD_FOLDER`: The directory where uploaded files are temporarily stored.
-   `ALLOWED_EXTENSIONS`: The set of allowed audio file extensions.
-   `MAX_FILE_SIZE`: The maximum allowed file size in bytes.

## Troubleshooting

-   **FFmpeg Errors**: If you encounter errors related to `ffmpeg`, ensure it is installed and accessible in your system's PATH. `ffmpeg` is required by `librosa` and `demucs` for loading various audio formats.
-   **GPU Not Detected**: If the application reports "CPU" mode but you have an NVIDIA GPU, verify that you have installed the correct CUDA-enabled version of PyTorch and that your NVIDIA drivers are up to date.
-   **Slow Performance**: Vocal separation and transcription are computationally intensive. Performance depends heavily on your hardware. Using a GPU will significantly speed up the process. For CPU-only users, selecting a lower transcription quality (`tiny` or `base`) will improve speed.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Changelog

See `CHANGELOG.md` for a history of changes.
