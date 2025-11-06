# AI-Powered Suno Prompt Generator

An advanced, AI-driven tool that analyzes any audio file to generate highly detailed, structured prompts for Suno AI. Features automated lyric extraction, vocal separation, and GPU acceleration for rapid results.

## Features

- **Comprehensive Audio Analysis**: Leverages modern AI libraries to extract tempo, key, energy, mood, and instrumental profiles from your audio.
- **Advanced Prompt Generation**: Creates multiple prompt variations, including a detailed "Advanced Mode" for Suno's Custom Mode.
  - Generates professional `[Tag: Value]` style prompts.
  - Creates structured lyric templates (`[INTRO]`, `[VERSE]`, `[CHORUS]`, etc.).
- **AI-Powered Vocal Separation**: Automatically isolates vocals from your track using Meta's `demucs` model for high-fidelity separation.
- **Automatic Lyrics Transcription**: Transcribes the extracted vocals using OpenAI's `Whisper`, with selectable quality levels for speed vs. accuracy.
- **Vocal Gender Detection**: Attempts to identify vocal pitch to suggest Male or Female lead vocals in the prompt.
- **Expanded Genre Library**: Includes a wide range of genres and subgenres, with a focus on electronic music (Trance, House, Drum & Bass, Hardcore, and more).
- **GPU Acceleration (PyTorch)**: Automatically uses an NVIDIA GPU for both vocal separation (`demucs`) and transcription (`Whisper`) to dramatically speed up analysis.
- **Real-time Progress Updates**: The frontend displays the current analysis step and a progress bar.
- **Hardware Detection**: The UI shows the detected CPU and GPU, and indicates whether GPU acceleration is active.
- **Configurable Quality**: Users can select the transcription quality to balance speed vs. accuracy.
- **Streamlined Build Process**: A dedicated GUI allows for easy building of the application, with an option to automatically run the executable after the build is complete.

## How It Works

The application follows a sophisticated pipeline to transform an audio file into a set of detailed prompts:

1.  **Upload & Pre-processing**: The user uploads an audio file through the web interface. The Flask backend receives the file and saves it to a temporary directory.
2.  **Audio Analysis (`librosa`)**: The `AudioAnalyzer` class loads the audio file and uses the `librosa` library to extract fundamental musical features, including:
    *   Tempo (BPM)
    *   Musical Key
    *   Energy (RMS)
    *   Spectral characteristics (centroid, rolloff)
    *   Zero-crossing rate
3.  **Genre & Mood Classification**: Based on the extracted features, a rule-based engine in `genre_rules.py` classifies the genre, and a separate algorithm determines the mood.
4.  **Vocal Detection & Separation (`demucs`)**: The system first detects the likelihood of vocals. If vocals are present, it uses the `demucs` model to separate the audio into distinct tracks (vocals, drums, bass, other).
5.  **Lyrics Transcription (`Whisper`)**: The isolated vocal track is passed to the `Whisper` model, which transcribes the lyrics. The user can select the model quality (`tiny`, `base`, `medium`) to balance speed and accuracy.
6.  **Prompt Generation**: The `PromptGenerator` class takes all the analyzed data (features, genre, mood, lyrics, etc.) and synthesizes it into multiple prompt variations, including a structured "Advanced Mode" prompt.
7.  **Streaming to Frontend**: The backend streams progress updates to the frontend in real-time, keeping the user informed of the current status.
8.  **Display Results**: The final analysis and generated prompts are displayed on the web page, ready for the user to copy and use in Suno.

## Dependencies

This project relies on several key Python libraries:

-   **Flask**: A micro web framework used for the backend server.
-   **Librosa**: A powerful library for audio analysis and feature extraction.
-   **Demucs**: Meta AI's state-of-the-art music source separation model.
-   **Whisper**: OpenAI's robust model for speech-to-text transcription.
-   **PyTorch**: The underlying deep learning framework for `demucs` and `Whisper`.
-   **Numpy**: For numerical operations on audio data.

## Installation from Source

This project requires **Python 3.10**.

### 1. Build the Source Distribution

First, build the source distribution by running the build script:

```bash
build_sdist.bat
```

This will create a `dist` folder containing a `.tar.gz` file.

### 2. Install the Package

1.  **Create a Virtual Environment**: It is crucial to use a virtual environment with Python 3.10.
    ```bash
    py -3.10 -m venv .venv
    ```

2.  **Activate the Environment**:
    ```bash
    .venv\Scripts\activate
    ```

3.  **Install the Package**: Install the package from the generated `.tar.gz` file.
    ```bash
    pip install dist/SunoPromptGenerator-1.0.0.tar.gz
    ```

4.  **(Optional) Install GPU Support**: For NVIDIA GPU acceleration, install the correct version of PyTorch.
    ```bash
    pip uninstall torch -y
    pip install torch==2.1.2 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    ```

5.  **Run the App**:
    ```bash
    python -m SunoPromptGenerator.app
    ```

6.  **Open Your Browser** to `http://localhost:5000`

## Usage

1.  Upload an audio file.
2.  Select your desired transcription quality.
3.  Wait for the analysis to complete, watching the real-time progress updates.
4.  Copy the generated prompts from the "Basic", "Detailed", or "Advanced Mode" cards.
5.  For "Advanced Mode", paste the "Style of Music" prompt into the corresponding field in Suno, and the "Lyrics Template" into the lyrics field.
6.  Edit and refine the prompts in Suno to create your music.

## Configuration

The application's settings can be modified in the `config.py` file:

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
