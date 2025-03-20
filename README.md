# YouTube Transcript Translation Tool

A Python utility that downloads audio from YouTube videos, transcribes it to SRT format, and translates the subtitles to a target language.

## Overview

This script performs three main functions:
1. Downloads audio from a YouTube video URL
2. Transcribes the audio to SRT subtitles using AssemblyAI
3. Translates the subtitles to a specified target language using Claude AI

The tool is designed to create multilingual subtitles for content while maintaining proper formatting and handling special content like Bible verses.

## Requirements

### API Keys

You'll need to obtain the following API keys:
- **AssemblyAI API Key**: For audio transcription
- **Anthropic Claude API Key**: For translation services

### Dependencies

- Python 3.6+
- Required Python packages:
  - yt-dlp
  - python-dotenv
  - assemblyai
  - anthropic
  - pyyaml

## Setup Instructions

### For All Platforms

1. Clone the repository or download the script

2. Create a `.env` file in the same directory as the script with your API keys:
   ```
   ASSEMBLY_AI_API_KEY=your_assemblyai_key_here
   CLAUDE_API_KEY=your_claude_key_here
   ```

3. Create the following directory structure:
   ```
   ├── scripts/
   │   └── translate-yt.py
   ├── content/     (downloaded audio files will be stored here)
   ├── lang/
   │   ├── en/      (English transcriptions)
   │   └── [target_lang]/  (translated files + config)
   │       └── config.yaml
   └── .env         (API keys)
   ```

### Linux/Mac Setup

1. Install Python 3.6 or higher:
   ```bash
   # For Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip
   
   # For MacOS using Homebrew
   brew install python3
   ```

2. Install required packages:
   ```bash
   pip3 install yt-dlp python-dotenv assemblyai anthropic pyyaml
   ```

3. Make the script executable:
   ```bash
   chmod +x scripts/translate-yt.py
   ```

### Windows Setup

1. Install Python 3.6+ from [python.org](https://www.python.org/downloads/windows/)

2. Install required packages:
   ```cmd
   pip install yt-dlp python-dotenv assemblyai anthropic pyyaml
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

Example for Spanish (`lang/es/config.yaml`):
```yaml
language: "Spanish"
bible_verse_translation: "Reina-Valera 1960"
translation_mapping:
  "Kingdom of God": "Reino de Dios"
  "Holy Spirit": "Espíritu Santo"
  "Christ Jesus": "Cristo Jesús"
```

* language - written in English
* bible_verse_translation - this will tell AI which bible translation will use if encountered with the Bible text. If the Bible translation is known, it will use it, otherwise it will translate as from the original source language
* translation_mapping - certain phrases can be generaly defined. If you want to enforce these phrases, define it in the config, AI will keep use these phrases and expression within the translation

## Usage

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