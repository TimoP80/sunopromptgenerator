# Changelog

## [1.2.0] - 2025-11-08

### Major Features

- **Native Windows GUI:** The application has been completely redesigned from a web-based interface to a native Windows GUI using `tkinter`. This removes the need for a web browser and provides a more integrated desktop experience. The new GUI is the default build and is launched via `gui.py`.
- **Updated Build Process:** The build system has been reconfigured to support the new GUI application. This includes new PyInstaller `.spec` files (`SunoPromptGenerator_gui.spec` and `SunoPromptGenerator_gui_noupx.spec`) and an updated `gui_builder.py` to create a standalone executable from the new GUI.
- **Metadata Display:** Added a "Quick Info" section to both the web and desktop GUIs. This feature provides immediate, lightweight analysis results—including tempo, key, and energy—upon file selection, offering users instant feedback before running the full analysis.
- **Enhanced Lyrics Template:** The advanced mode's lyrics template has been significantly improved. It now generates more creative and context-aware suggestions based on the song's mood, genre, and energy, providing a more inspiring starting point for lyric writing.
- **Expanded Whisper Models:** The list of available Whisper models has been expanded to include `small`, `large`, and the English-only variants (`.en`). This provides users with more granular control over transcription speed and quality.
- **Genre Enhancement:** Expanded the genre-specific instrumentation and style tags for Gabberdisco, Hardcore, Hard Techno, and House to generate more detailed and authentic prompts.
- **Web App GPU Acceleration:** The web application now correctly detects and utilizes the available GPU for AI processing tasks, ensuring that Whisper transcriptions are properly hardware-accelerated.
- **Tempo Analysis:** Implemented a fallback mechanism in the tempo analysis to ensure a valid BPM is always returned, improving the reliability of the prompt generation.
- **Analysis Display:** Fixed a bug where the analysis results (Tempo, Key, Energy) were not displaying correctly in the web UI. The backend JSON response has been restructured to ensure the data is properly parsed and displayed.

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