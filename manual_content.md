# SunoPromptGenerator User Manual

---

## Chapter 1: Introduction

### 1.1. What is the SunoPromptGenerator (AI Music Studio)?

Welcome to the SunoPromptGenerator, also known as the AI Music Studio. This advanced tool is designed to bridge the gap between your favorite audio tracks and the creative potential of AI-powered music generation. It acts as a musical analyst, listening to an audio file, understanding its core components, and translating them into detailed text prompts that you can use with the Suno music generation API.

### 1.2. Core Purpose & Key Concepts

The primary goal of the SunoPromptGenerator is to automate the complex process of describing a song's style, mood, and structure. Instead of manually trying to put the "vibe" of a song into words, this tool does the heavy lifting for you. It analyzes an audio file to extract its fundamental musical and lyrical characteristics, enabling you to create new, original music that is thematically and musically inspired by a reference track.

### 1.3. Who is this manual for?

This manual is for anyone interested in creating AI-generated music, especially those who want to guide the AI with the style of an existing song. It is written for a non-technical audience, so you don't need a background in music theory or software development to get started.

---

## Chapter 2: Getting Started

### 2.1. System Requirements

#### 2.1.1. Operating Systems
The application is compatible with most modern operating systems, including Windows, macOS, and Linux.

#### 2.1.2. Hardware Acceleration (NVIDIA GPU Support)
For the best performance, an NVIDIA GPU is highly recommended. The application can leverage the GPU to significantly speed up demanding tasks like vocal separation and lyric transcription. If no compatible GPU is detected, the application will use the CPU, which will be noticeably slower.

### 2.2. Installation

#### 2.2.1. Installing the Application
Follow the installation instructions provided in the `README.md` file that came with the application. This typically involves running an installer or using a package manager.

#### 2.2.2. Setting up the Suno API Key
To generate music directly from the application, you will need a Suno API key. Once you have your key, enter it into the settings or configuration section of the application.

#### 2.2.3. Building from Source (Optional)

For advanced users who wish to build the application from the source code, the project includes convenient batch scripts. This process requires a Python environment to be set up.

1.  **Set up the Environment:** First, create and activate a Python virtual environment to manage dependencies.
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

2.  **Install Dependencies:** Install the required Python packages.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Build Script:**
    -   To build the standard **GUI application**, run `build_gui.bat`.
    -   To build the **command-line version**, run `build_cli.bat`.

The final executable will be located in the `dist` folder.

### 2.3. A Quick Tour of the Interface

The SunoPromptGenerator offers two user-friendly interfaces:

#### 2.3.1. The Web Interface (Flask)
Accessible through your web browser, this interface is perfect for users who prefer a modern, web-based experience.

#### 2.3.2. The Desktop GUI (Tkinter)
A standalone desktop application that provides a classic, native window experience for offline use. Both interfaces offer the same core functionality.

---

## Chapter 3: Your First Music Prompt (Quick Start Guide)

This guide will walk you through creating your first prompt in five simple steps.

### 3.1. Step 1: Selecting Your Audio File
Click the "Browse" or "Select File" button to open your computer's file browser. Choose an audio file you want to analyze (e.g., `.mp3`, `.wav`, `.flac`).

### 3.2. Step 2: Configuring Analysis Options (Basic)
For your first run, you can leave the default settings as they are. The application is pre-configured to provide a good balance of speed and quality.

### 3.3. Step 3: Running the Analysis
Click the "Analyze" button. You will see a progress bar and status updates as the application works through its steps, such as "Analyzing audio features...", "Separating vocals...", and "Generating prompts...".

### 3.4. Step 4: Understanding and Copying Your First Prompt
Once the analysis is complete, the results will appear. Go to the "Generated Prompts" tab. You will see several variations. The "Basic Prompt" is a great starting point. Click the "Copy" button next to it.

### 3.5. Step 5 (Optional): Generating Music with the Suno API
If you have entered your Suno API key, you can click the "Generate Music" button next to any prompt. The application will send the prompt to Suno and track the progress of your new song's creation.

---

## Chapter 4: The User Interface in Detail

### 4.1. The Main Window / Home Page

#### 4.1.1. File Selection Area
This is where you begin. It contains the button to select the audio file you wish to analyze.

#### 4.1.2. Configuration Panel
Here, you can fine-tune the analysis process. You can force a specific genre, choose the quality of the AI models, and select other output options.

#### 4.1.3. The "Analyze" Button
The main action button that starts the entire analysis pipeline.

#### 4.1.4. Progress Bar and Status Updates
These elements provide real-time feedback during the analysis, so you know what's happening and how long it might take.

### 4.2. The Results View

After analysis, the results are organized into three tabs for clarity.

#### 4.2.1. Generated Prompts Tab
This is the primary output. It contains all the different text prompts created from your audio file, ready to be copied or sent to the Suno API.

#### 4.2.2. Analysis Data Tab
This tab provides a detailed breakdown of all the musical characteristics extracted from the file, such as tempo, key, mood, and detected instruments.

#### 4.2.3. Log Tab
The log provides a step-by-step history of the analysis process, which can be useful for troubleshooting or understanding the workflow.

---

## Chapter 5: Core Features Explained

### 5.1. Comprehensive Audio Analysis

The application uses the powerful `librosa` library to perform a deep dive into the music's structure.

- **5.1.1. Tempo (BPM) Detection:** Measures the speed of the music in Beats Per Minute.
- **5.1.2. Musical Key and Mode:** Determines the track's key (e.g., C, G#, F) and mode (Major or minor).
- **5.1.3. Energy Classification:** Analyzes the track's loudness (RMS value) to classify it as "low," "medium," or "high" energy.
- **5.1.4. Mood Inference:** Combines tempo, key, and energy to infer the overall mood, such as "Energetic," "Melancholic," or "Calm."
- **5.1.5. Automatic Genre Classification:** A smart, rule-based engine identifies the genre from a large library, with a special focus on electronic music.

### 5.2. Vocal and Lyric Processing

- **5.2.1. How Vocal Separation Works (`demucs`):** The application uses Meta's high-fidelity `demucs` model to cleanly separate the vocal track from the instruments.
- **5.2.2. Lyric Transcription with Whisper:** The isolated vocal track is then transcribed into text using OpenAI's `Whisper` model.
- **5.2.3. Vocal Gender Detection:** By analyzing the pitch of the separated vocals, the tool suggests whether the lead singer is "Male" or "Female."

### 5.3. Understanding the Generated Prompts

- **5.3.1. Basic & Detailed Prompts:** Simple, comma-separated lists of the core musical attributes.
- **5.3.2. Thematic & Artist-Style Prompts:** More creative variations that might describe a scene (e.g., "a late-night drive") or emulate the style of a famous artist.
- **5.3.3. Advanced Mode Prompts (Custom Mode):** A highly structured format for Suno's Custom Mode. It generates two parts: a `[Tag: Value]` style prompt for musical direction and a detailed lyrics template with structural markers like `[INTRO]`, `[VERSE]`, and `[CHORUS]`.

---

## Chapter 6: Advanced Usage & Configuration

### 6.1. Interacting with the Suno API

- **6.1.1. Sending Prompts to the API:** Click the "Generate Music" button next to any prompt to start the creation process.
- **6.1.2. Monitoring Generation Status:** The interface will show the status of your generation jobs (e.g., "queued," "processing," "complete").
- **6.1.3. Accessing Your Generated Audio:** Once complete, the application will display links to the final audio files for you to listen to and download.

### 6.2. Detailed Configuration Options

- **6.2.1. Forcing a Specific Genre:** If you disagree with the auto-detected genre or want to experiment, you can select a specific genre from the dropdown menu before analysis.
- **6.2.2. Choosing a Whisper Model:** Select a model size (`tiny`, `base`, `medium`) to balance transcription speed and accuracy. Larger models are more accurate but slower.
- **6.2.3. Selecting a Vocal Separation Model:** Choose the quality of the `demucs` model for vocal separation.
- **6.2.4. Saving the Isolated Vocal Track:** Check this option to save the separated vocals as a separate `.wav` file, which is great for remixes or sampling.

### 6.3. Working with Inputs and Outputs

- **6.3.1. Supported Input Audio Formats:** The tool supports most common audio formats, including MP3, WAV, FLAC, and OGG.
- **6.3.2. Exporting Analysis Data (JSON):** You can export the detailed analysis data as a JSON file for use in other applications or for your own records.
- **6.3.3. Managing Optional Outputs:** The optional vocal `.wav` file will be saved in a designated output folder.

---

## Chapter 7: Troubleshooting and FAQ

### 7.1. Frequently Asked Questions (FAQ)

- **"Why is the analysis so slow?"**
  Vocal separation and lyric transcription are very demanding tasks. Performance depends heavily on your computer's hardware. Using an NVIDIA GPU will result in a dramatic speed increase. If you don't have one, the process will take longer.

- **"Why was the genre detected incorrectly?"**
  Genre detection is complex and subjective. Our rule-based engine is very capable but may not always be perfect. If you find the genre is wrong, you can easily override it by selecting the correct one from the genre list before running the analysis.

- **"How can I improve lyric transcription accuracy?"**
  In the configuration panel, select a larger "Whisper Model" (e.g., `medium` or `large`). Larger models are significantly more accurate but require more processing time and computer memory.

### 7.2. Common Errors and Solutions

- **7.2.1. Installation Issues:** Ensure you have followed all steps in the `README.md` file and have installed all required dependencies.
- **7.2.2. API Connection Errors:** Double-check that you have entered your Suno API key correctly and that you have a stable internet connection.
- **7.2.3. Errors during Audio Analysis:** Some audio files may be corrupt or in an unsupported format. Try converting the file to a standard format like `.mp3` or `.wav` and try again.

---

## Appendix

### A.1. Full List of Detectable Genres
The application includes a large, expandable library of genres with a particular focus on electronic music styles. Please refer to the genre selection dropdown in the application for a complete list.

### A.2. Glossary of Musical Terms
- **Tempo:** The speed of a piece of music, measured in Beats Per Minute (BPM).
- **Key:** The group of pitches, or scale, that forms the basis of a music composition.
- **RMS (Root Mean Square):** A measure of the average power or loudness of an audio signal, used by the application to determine the track's "energy."