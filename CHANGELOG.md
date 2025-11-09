# Changelog

## [1.4.0] - 2025-11-09

### Major Features

- **Application Overhaul:**
  - **Native GUI:** Replaced the web interface with a native `tkinter` GUI for a more integrated desktop experience.
  - **Suno API Integration:** Added the ability to generate music directly from prompts using the Suno API.
  - **Rebranding:** Renamed the application to "AI Music Studio" to reflect its new capabilities.

- **Build System:**
  - **Flexible Builds:** Introduced separate build scripts (`build_gui.bat`, `build_cli.bat`) with options to toggle UPX compression.
  - **Self-Contained:** The build process now automatically bundles pretrained models, making the application fully offline-capable.
  - **Streamlined:** Removed redundant `.spec` files and updated the GUI builder for a cleaner, more maintainable project.

- **Prompt Generation & Analysis:**
  - **Creative Engine:** Overhauled the prompt generation logic with a new genre-based instrument mapping system, expanded descriptor maps, and more dynamic thematic prompts.
  - **Advanced Analysis:** Implemented a more accurate key-finding algorithm, expanded tempo descriptors, and included more detailed metrics in the analysis output.
  - **Powerful Refinement:** The "Refinement Prompt" is now a data-driven feedback loop, generating prescriptive prompts with exact numerical data for precise iterative control.
  - **Enhanced Lyrics:** The lyrics template now generates more creative and context-aware suggestions.

- **User Experience & Performance:**
  - **UI Redesign:** The web interface now features a tabbed layout, and both GUIs include a "Quick Info" section for instant metadata display.
  - **Vocal Separation:** Added an option to save isolated vocal tracks.
  - **Performance Options:** Users can now select a faster Demucs model for quicker analysis.
  - **GPU & CUDA:** Optimized CUDA processing with mixed-precision inference and memory management for a faster, more stable experience.
  - **Expanded Models:** Added more Whisper model options for greater control over transcription speed and quality.
### Bug Fixes

- **CLI Arguments:** Resolved an issue where the command-line interface would not correctly parse arguments with spaces.
- **Analysis Display:** Fixed a bug where the analysis results (Tempo, Key, Energy) were not displaying correctly in the web UI. The backend JSON response has been restructured to ensure the data is properly parsed and displayed.
- **Instrument Detection:** Resolved a `NameError` in the `detect_instruments` method caused by a missing `import random` statement, ensuring the analysis process completes successfully.
- **JSON Serialization:** Fixed a `TypeError` in the JSON serialization of analysis data by ensuring all NumPy `float32` values are converted to standard Python floats.
- **GUI:** Restored the "Generate Music" buttons to the web GUI, which were inadvertently removed during a redesign.
- **Build:** Updated the build scripts to use the new application name ("AIMusicStudio"), ensuring the executable is correctly named.
- **Dependencies:** Added `tensorboard` to the project's dependencies to resolve a `ModuleNotFoundError` that was causing the build to fail.

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