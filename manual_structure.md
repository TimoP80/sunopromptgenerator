# SunoPromptGenerator User Manual - Table of Contents

## Chapter 1: Introduction
- 1.1. What is the SunoPromptGenerator (AI Music Studio)?
- 1.2. Core Purpose & Key Concepts
- 1.3. Who is this manual for?

## Chapter 2: Getting Started
- 2.1. System Requirements
    - 2.1.1. Operating Systems
    - 2.1.2. Hardware Acceleration (NVIDIA GPU Support)
- 2.2. Installation
    - 2.2.1. Installing the Application
    - 2.2.2. Setting up the Suno API Key
    - 2.2.3. Building from Source (Optional)
- 2.3. A Quick Tour of the Interface
    - 2.3.1. The Web Interface (Flask)
    - 2.3.2. The Desktop GUI (Tkinter)

## Chapter 3: Your First Music Prompt (Quick Start Guide)
- 3.1. Step 1: Selecting Your Audio File
- 3.2. Step 2: Configuring Analysis Options (Basic)
- 3.3. Step 3: Running the Analysis
- 3.4. Step 4: Understanding and Copying Your First Prompt
- 3.5. Step 5 (Optional): Generating Music with the Suno API

## Chapter 4: The User Interface in Detail
- 4.1. The Main Window / Home Page
    - 4.1.1. File Selection Area
    - 4.1.2. Configuration Panel
    - 4.1.3. The "Analyze" Button
    - 4.1.4. Progress Bar and Status Updates
- 4.2. The Results View
    - 4.2.1. Generated Prompts Tab
    - 4.2.2. Analysis Data Tab
    - 4.2.3. Log Tab

## Chapter 5: Core Features Explained
- 5.1. Comprehensive Audio Analysis
    - 5.1.1. Tempo (BPM) Detection
    - 5.1.2. Musical Key and Mode
    - 5.1.3. Energy Classification (Low, Medium, High)
    - 5.1.4. Mood Inference
    - 5.1.5. Automatic Genre Classification
- 5.2. Vocal and Lyric Processing
    - 5.2.1. How Vocal Separation Works (`demucs`)
    - 5.2.2. Lyric Transcription with Whisper
    - 5.2.3. Vocal Gender Detection
- 5.3. Understanding the Generated Prompts
    - 5.3.1. Basic & Detailed Prompts
    - 5.3.2. Thematic & Artist-Style Prompts
    - 5.3.3. Advanced Mode Prompts (Custom Mode)
        - Understanding `[Tag: Value]` Structure
        - Working with the Lyrics Template (`[INTRO]`, `[VERSE]`, etc.)

## Chapter 6: Advanced Usage & Configuration
- 6.1. Interacting with the Suno API
    - 6.1.1. Sending Prompts to the API
    - 6.1.2. Monitoring Generation Status
    - 6.1.3. Accessing Your Generated Audio
- 6.2. Detailed Configuration Options
    - 6.2.1. Forcing a Specific Genre
    - 6.2.2. Choosing a Whisper Model (Speed vs. Accuracy)
    - 6.2.3. Selecting a Vocal Separation Model
    - 6.2.4. Saving the Isolated Vocal Track
- 6.3. Working with Inputs and Outputs
    - 6.3.1. Supported Input Audio Formats
    - 6.3.2. Exporting Analysis Data (JSON)
    - 6.3.3. Managing Optional Outputs (Vocal `.wav` file)

## Chapter 7: Troubleshooting and FAQ
- 7.1. Frequently Asked Questions (FAQ)
    - "Why is the analysis so slow?"
    - "Why was the genre detected incorrectly?"
    - "How can I improve lyric transcription accuracy?"
- 7.2. Common Errors and Solutions
    - 7.2.1. Installation Issues
    - 7.2.2. API Connection Errors
    - 7.2.3. Errors during Audio Analysis

## Appendix
- A.1. Full List of Detectable Genres
- A.2. Glossary of Musical Terms (Tempo, Key, RMS, etc.)