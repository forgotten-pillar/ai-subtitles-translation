# YouTube Transcript Translation Tool

A Python utility that downloads audio from YouTube videos, transcribes it to SRT format, and translates the subtitles to a target language.

## Overview

This script performs three main functions:
1. Downloads audio from a YouTube video URL
2. Transcribes the audio to SRT subtitles using AssemblyAI
3. Translates the subtitles to a specified target language using Claude AI

The tool is designed to create multilingual subtitles for content while maintaining proper formatting and handling special content like Bible verses.

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/forgotten-pillar/ai-subtitles-translation.git
cd ai-subtitles-translation
```

### API Keys

You'll need to obtain the following API keys:
- **AssemblyAI API Key**: Sign up and get your key at [assemblyai.com](https://www.assemblyai.com/)
- **Anthropic Claude API Key**: Sign up and get your key at [console.anthropic.com](https://console.anthropic.com/)

### Prerequisites

- **FFmpeg**: Required for audio processing
- Python 3.6+

### Dependencies

- Python 3.6+
- Required Python packages:
  - yt-dlp
  - python-dotenv
  - assemblyai
  - anthropic
  - pyyaml

## Setup Instructions

### Setting Up Python Virtual Environment

#### For Linux/Mac
```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install yt-dlp python-dotenv assemblyai anthropic pyyaml
```

#### For Windows
```cmd
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate

# Install dependencies
pip install yt-dlp python-dotenv assemblyai anthropic pyyaml
```

### Environment Configuration

Create a `.env` file in the root directory with your API keys:
```
ASSEMBLY_AI_API_KEY=your_assemblyai_key_here
CLAUDE_API_KEY=your_claude_key_here
```

### Directory Structure

Ensure your project has the following directory structure:
```
├── scripts/
│   └── translate-yt.py
├── content/     (downloaded audio files will be stored here)
├── lang/
│   ├── en/      (English transcriptions)
│   └── [target_lang]/  (translated files + config)
│       └── config.yaml
├── venv/        (virtual environment)
└── .env         (API keys)
```

### Platform-Specific Setup

#### Linux/Mac Setup

1. Install FFmpeg and Python 3.6+:
   ```bash
   # For Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip ffmpeg
   
   # For MacOS using Homebrew
   brew install python3 ffmpeg
   ```

2. Make the script executable:
   ```bash
   chmod +x scripts/translate-yt.py
   ```

#### Windows Setup

1. Install Python 3.6+ from [python.org](https://www.python.org/downloads/windows/)

2. Install FFmpeg:
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use a package manager like Chocolatey
   - Add FFmpeg to your system PATH

   With Chocolatey:
   ```cmd
   choco install ffmpeg
   ```

## Translation Configuration

Create a `config.yaml` file in the `lang/[target_lang]/` directory with the following structure:

```yaml
language: "Target Language Name"
bible_verse_translation: "Bible Translation Name for Target Language"
translation_mapping:
  "Source term 1": "Target language translation 1"
  "Source term 2": "Target language translation 2"
  # Add more specific terms that need consistent translation
```

### Config File Parameters Explained

- **language**: The name of the target language written in English (e.g., "Spanish", "French", "German")

- **bible_verse_translation**: Specifies which Bible translation to use when translating biblical content.
  - If the specified translation exists in the target language, the AI will use it directly
  - If the translation doesn't exist, the AI will translate the text from the original source language
  - Example: "Reina-Valera 1960" for Spanish, "Luther Bibel 2017" for German

- **translation_mapping**: A dictionary of specific phrases and their enforced translations
  - This ensures consistency in how certain key terms are translated throughout the content
  - The AI will always use these specified translations when encountering the defined source phrases
  - Particularly useful for specialized terminology, proper nouns, or conceptual terms with specific translations in the target language

Example for Spanish (`lang/es/config.yaml`):
```yaml
language: "Spanish"
bible_verse_translation: "Reina-Valera 1960"
translation_mapping:
  "Kingdom of God": "Reino de Dios"
  "Holy Spirit": "Espíritu Santo"
  "Christ Jesus": "Cristo Jesús"
  "faith": "fe"
  "grace": "gracia"
```

Example for German (`lang/de/config.yaml`):
```yaml
language: "German"
bible_verse_translation: "Luther Bibel 2017"
translation_mapping:
  "Kingdom of God": "Reich Gottes"
  "Holy Spirit": "Heiliger Geist"
  "gospel": "Evangelium"
```

## Usage

Remember to activate your virtual environment before running the script:

```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

Then run the script:
```bash
python scripts/translate-yt.py <youtube-url> <target-language-code>
```

Example:
```bash
python scripts/translate-yt.py https://www.youtube.com/watch?v=example es
```

This will:
1. Download the audio from the YouTube video
2. Transcribe it to SRT format in English
3. Translate the SRT to Spanish using the configuration in `lang/es/config.yaml`
4. Save both the English and Spanish SRT files in their respective language folders

## Output Files

The script creates the following files:
- Original audio file in the `content/` directory
- English SRT file in the `lang/en/` directory
- Translated SRT file in the `lang/[target_lang]/` directory with the naming format `[video_title]_[TARGET_LANG].srt`

## Notes

- If a file already exists (audio or SRT), the script will skip processing it
- Translations are performed in batches of 200 subtitles at a time
- The script normalizes line breaks in SRT files for proper formatting
- English cannot be selected as a target language