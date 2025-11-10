# Changelog

## [2.0.0] - 2025-11-10

### Added

- **New Web Interface &amp; Flask Backend:** A modern, single-page web application served by a robust Flask backend (`app.py`), exposing a REST API and using a `waitress` server.
- **Official Suno API v1 Integration:** The application now uses the official Suno API via the new `suno_client.py` module, which handles authenticated requests and error handling.
- **Advanced Music Generation &amp; Workflow:**
    - "Quick Generation" to create music directly from text prompts.
    - Full support for Suno's "Custom Mode" with distinct inputs for "Style of Music" and "Lyrics".
    - Asynchronous music generation with API polling.
- **Enhanced User Experience:**
    - Real-time progress updates and a progress bar for the analysis process.
    - A two-step analysis workflow showing "Quick Info" (metadata) before the full analysis.
    - Separate, slide-out panels for "Analysis History" and "Generation History".
    - Waveform visualization for uploaded audio files using WaveSurfer.js.
- **Account &amp; Settings Management:**
    - Multi-account support with the ability to add, remove, and set a default account.
    - Automatic fetching and display of remaining Suno credits.
- **Improved Audio Analysis &amp; Prompt Generation:**
    - Vocal gender detection from separated vocal tracks.
    - Updated prompt generation logic for Suno v5, including "Thematic" and "Refinement" variations.
    - Generation of a structured lyrics template with metadata and timestamps.
- **Standalone Desktop GUI:** A responsive desktop application (`gui.py`) is available, using `multiprocessing` for background analysis and an integrated `pygame` audio player.

### Changed

- **Architectural Overhaul:** The application has been transformed from a monolithic script into a modular client-server application.
- **Project Structure &amp; Portability:** The project is now modularized, and pretrained models are cached locally for portability.

## [1.5.0] - 2025-11-10

### Added

- **Complete Suno API Migration:** Overhauled the entire application to use the official Suno API (`docs.sunoapi.org`). This involved rewriting the `suno_client`, updating the `gui.py` to handle new data structures, and aligning the `app.py` backend to the new API workflows for music generation, status checking, and credit retrieval.

### Fixed

- **Suno API Client:**
  - Corrected the credits endpoint from `/get-credits` to `/credits/get-credits-info` to resolve 404 errors.
  - Added specific error handling for `HTTP 429` to gracefully manage rate-limiting.
  - Enhanced the `generate_music` function to accept a `model` parameter for more flexible version control.
  - Improved the `get_credits` function to return the full JSON response, providing more detailed credit information.
## [1.4.0] - 2025-11-09

### Major Features

- **Application Overhaul:** Replaced the web UI with a native `tkinter` GUI, integrated the Suno API for music generation, and rebranded the app to "AI Music Studio".
- **Build System:** Introduced separate, streamlined build scripts (`build_gui.bat`, `build_cli.bat`) that bundle all models, making the application fully self-contained and offline-capable.
- **Prompt Generation & Analysis:** Overhauled the prompt engine with genre-based mapping and more dynamic themes. Implemented a more accurate key-finding algorithm and a data-driven "Refinement Prompt" for precise control.
- **UX & Performance:** Redesigned the UI with a "Quick Info" panel for instant metadata. Added options to save vocal tracks, select faster Demucs models, and choose from more Whisper models. Optimized GPU/CUDA processing for better performance.

### Bug Fixes

- **CLI Arguments:** Resolved an issue where the command-line interface would not correctly parse arguments with spaces.
- **Analysis Display:** Fixed a bug where the analysis results (Tempo, Key, Energy) were not displaying correctly in the web UI. The backend JSON response has been restructured to ensure the data is properly parsed and displayed.
- **Instrument Detection:** Resolved a `NameError` in the `detect_instruments` method caused by a missing `import random` statement, ensuring the analysis process completes successfully.
- **JSON Serialization:** Fixed a `TypeError` in the JSON serialization of analysis data by ensuring all NumPy `float32` values are converted to standard Python floats.
- **GUI:** Restored the "Generate Music" buttons to the web GUI, which were inadvertently removed during a redesign.
- **Build:** Updated the build scripts to use the new application name ("AIMusicStudio"), ensuring the executable is correctly named.
- **Dependencies:** Added `tensorboard` to the project's dependencies to resolve a `ModuleNotFoundError` that was causing the build to fail.

### Documentation

- **README:** Overhauled the `README.md` to reflect all the new features and changes in version `1.4.0`.

## [1.1.0] - 2025-11-07

### Added

- **Two-Step Analysis Workflow:** Implemented a new two-step analysis process. The application now performs a quick preprocessing pass to display basic audio metadata before proceeding with the full analysis.
- **Metadata Display:** The UI now displays key metadata (duration, sample rate, channels) after a file is uploaded, providing instant feedback.
- **JSON Export:** Added a feature to export the complete analysis results to a `analysis.json` file. The export now includes all generated prompts and the full, raw analysis data for more detailed insights.
- **Comprehensive Metadata Extraction:** The preprocessing step now extracts and displays all available metadata from the audio file's tags, providing a complete overview of the track's information before the full analysis begins.
- **Splash Screen:** Added a splash screen to the executable, providing visual feedback that the application is launching. The splash screen now displays status messages during the initialization process.

### Fixed

- **Audio Analysis Crash:** Resolved a critical `AttributeError` during tempo analysis caused by an incompatibility between `librosa` and newer versions of `scipy`. The application would crash because `librosa` was trying to use a function (`scipy.signal.hann`) that has been removed. This has been fixed by pinning `scipy` to version `1.11.4`.
- **Build Process:** Overhauled the PyInstaller build process to resolve critical build failures. This includes fixing the `torchaudio` and `torio` hooks, updating the `.spec` file to correctly bundle all necessary data files (like `ffmpeg` libraries), and improving the `build.bat` script for better reliability.
- **Executable Hanging:** Fixed a critical issue where the compiled executable would hang on startup due to a multiprocessing conflict. The application now correctly isolates the server initialization logic, ensuring a stable launch.
- **GUI Builder Crash:** Resolved an `AttributeError` that caused the `build_with_gui.bat` script to crash on launch. The GUI builder is now fully functional.
- **Build Script "Access Denied" Error:** The GUI builder now forcefully terminates any running instances of the application before cleaning the build directory, preventing "Access is denied" errors.
- **GUI GPU Acceleration:** The native Windows GUI was not properly configured to use the GPU for AI processing. This has been fixed by updating the application to detect and utilize the available GPU, ensuring that Demucs and Whisper operations are hardware-accelerated.
- **Build Output Path:** The PyInstaller build script was attempting to write to a protected system directory, causing a `PermissionError`. This has been corrected by explicitly setting the output paths to the local project directory, ensuring a successful build.