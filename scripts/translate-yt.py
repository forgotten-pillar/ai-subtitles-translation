import os
import sys
import yt_dlp
from dotenv import load_dotenv
import assemblyai as aai
import re
from anthropic import Anthropic
import yaml

# Load enviroment variables from .env file
load_dotenv()

def split_srt_into_batches(srt_content, batch_size=200):
    srt_content = srt_content.strip()
    subtitles = re.split(r'\n(?=\d+\n\d{2}:\d{2}:\d{2},\d{3} -->)', srt_content)
    batches = [subtitles[i:i + batch_size] for i in range(0, len(subtitles), batch_size)]
    return ["\n".join(batch) + "\n" for batch in batches]

def get_config_value(yaml_path, value_name):
    if not yaml_path:
        sys.exit("Error: No YAML configuration file path provided.")
    if not os.path.exists(yaml_path):
        sys.exit(f"Error: YAML configuration file '{yaml_path}' does not exist.")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        sys.exit(f"Error: Failed to load YAML file: {e}")
    if not config or value_name not in config:
        sys.exit(f"Error: '{value_name}' variable is missing in the YAML file.")
    return config[value_name]

def read_srt(srt_file):
    with open(srt_file, 'r', encoding='utf-8') as file:
        srt_content = file.read()
    return srt_content

def normalize_line_breaks(srt_path):
    with open(srt_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Ensure exactly one blank line between subtitle blocks
    fixed_content = re.sub(r'\n{2,}(?=\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})', '\n', content.strip()) + '\n'
    
    # Ensure each subtitle text ends with a single blank line before the next block
    fixed_content = re.sub(r'([^\n])\n(\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})', r'\1\n\n\2', fixed_content)
    
    with open(srt_path, 'w', encoding='utf-8') as file:
        file.write(fixed_content)
    
    print(f"Normalized line breaks in: {srt_path}")

def create_systerm_prompot(translation_config):
    language = get_config_value(translation_config, "language")
    translation_mapping = get_config_value(translation_config, "translation_mapping")
    bible_verse_translation = get_config_value(translation_config, "bible_verse_translation")

    mapping_text = ""
    mapping_lines = []

    # check if translation_mapping is array
    if isinstance(translation_mapping, dict):
        
        for src, tgt in translation_mapping.items():
            mapping_lines.append(f'   - "{src}" → "{tgt}"')
        mapping_text = "\n".join(mapping_lines)

    mapping_rule = f"""
    2. **Translation Mapping:**
        - For the following words or phrases, use the provided translations:
        {mapping_text}
    """ if len(mapping_lines) > 0 else ""

    return f"""
    You are SRT title translator. Translate to {language} language. Output only SRT format.

    Key rules to follow:
    1. **Bible verse Translations:**
        - For every Bible verse encountered, use "{bible_verse_translation}" Bible translation.
    
    {mapping_rule}

    Follow these instructions carefully to ensure that the translation is accurate and free of any extraneous commentary.
    """

def translate_batch(client, batch, system_prompt):
    
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=8192,
        temperature=0,
        system=system_prompt,
        messages=[{"role": "user", "content": batch}]
    )

    translation_response = message.content
    if isinstance(translation_response, list) and translation_response:
        translation_response = translation_response[0]
    if hasattr(translation_response, 'text'):
        translation_response = translation_response.text

    return translation_response


def get_output_filename(url, output_dir):
    """
    Get the expected filename without downloading
    
    Args:
        url (str): YouTube URL
        output_dir (str): Directory where file would be saved
        
    Returns:
        str: Expected filename path (without extension)
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'skip_download': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info['title']
        sanitized_title = ydl.prepare_filename(info).split(os.path.sep)[-1].split('.')[0]
        return sanitized_title

def download_audio(url, output_dir):
    """
    Download audio from a YouTube URL if it doesn't already exist
    
    Args:
        url (str): YouTube URL to download audio from
        output_dir (str): Directory to save the audio file
        
    Returns:
        str or None: Path to the file (either existing or newly downloaded),
                     or None if an error occurred
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # First check if file already exists (as .mp3)
    try:
        base_filename = get_output_filename(url, output_dir)
        mp3_path = os.path.join(output_dir, f"{base_filename}.mp3")
        webm_path = os.path.join(output_dir, f"{base_filename}.webm")
        
        if os.path.exists(mp3_path):
            print(f"File already exists as MP3: {mp3_path}")
            print("Skipping download...")
            return mp3_path
        elif os.path.exists(webm_path):
            print(f"File already exists as WebM: {webm_path}")
            print("Skipping download...")
            return webm_path
    except Exception as e:
        print(f"Error checking file existence: {str(e)}")
        # Continue with download attempt if we can't check properly
    
    print(f"Downloading audio from: {url}")
    output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
    
    # Configure yt-dlp options for WebM download without conversion
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False
    }
    
    # Download the audio file
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            print(f"Audio downloaded successfully: {filename}")
            return filename
    except Exception as e:
        print(f"Error downloading audio: {str(e)}")
        return None

def setup_directories(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def transcribe(media_file):
    assembly_api_key = os.getenv("ASSEMBLY_AI_API_KEY")

    if assembly_api_key is None:
        print("Assembly AI API Key not found in .env file")
        sys.exit(1)
    
    aai.settings.api_key = assembly_api_key

    print(f"Transcribing {media_file}...")
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(media_file)

    srt_content = transcript.export_subtitles_srt()
    
    print("Transcription complete")

    return srt_content

def translate_srt(srt_content, translation_config):
    system_prompt = create_systerm_prompot(translation_config)
    
    # Get the API key from the environment (.env file).
    claude_api_key = os.environ.get("CLAUDE_API_KEY")
    if not claude_api_key:
        sys.exit("Error: CLAUDE_API_KEY not set in .env file.")
    
    client = Anthropic(api_key=claude_api_key)
    
    print(f"System prompt: {system_prompt}")
    print("Translating SRT content...")
    batches = split_srt_into_batches(srt_content)
    
    translated_batches = []
    batch_count = len(batches)
    batch_index = 0
    for batch in batches:
        batch_index += 1
        print(f"Translating batch {batch_index} of {batch_count}...")
        translation_response = translate_batch(client, batch, system_prompt)
        translated_batches.append(translation_response)
    
    print("Translation complete")
    return "\n".join(translated_batches)

def main():
    # The assumption is that source language is English
    if len(sys.argv) < 3:
        print("Usage: python download-audio.py <youtube-url> <target-lang>")
        sys.exit(1)
    
    url = sys.argv[1]
    target_lang = sys.argv[2]

    if(target_lang == 'en'):
        print("Target language cannot be English")
        return 1
    
    # Get script directory and construct path to content directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    content_dir = os.path.join(root_dir, "content")
    setup_directories(content_dir)

    output_source_lang_dir = os.path.join(root_dir, "lang", "en")
    setup_directories(output_source_lang_dir)

    output_target_lang_dir = os.path.join(root_dir, "lang", target_lang)
    
    # Download the audio file
    media_file = download_audio(url, content_dir)
    
    media_name = os.path.basename(media_file)
    media_name = os.path.splitext(media_name)[0]

    if not media_file:
        print("Download failed.")
        return 1
    
    print(f"File path: {media_file}")

    source_lang_srt_file = os.path.join(output_target_lang_dir, f"{media_name}.srt")

    if os.path.exists(source_lang_srt_file):
        print(f"Output file {source_lang_srt_file} already exists")
        return 1

    # Transcribe the audio file
    source_srt_content = transcribe(media_file)

    with open(source_lang_srt_file, 'w', encoding='utf-8') as file:
        file.write(source_srt_content)
    
    print(f"Transcription saved to: {source_lang_srt_file}")
    
    normalize_line_breaks(source_lang_srt_file)

    # load translation configuration
    translation_config = os.path.join(root_dir, "lang", target_lang, "config.yaml")
    if not os.path.exists(translation_config):
        print(f"Translation configuration file {translation_config} not found")
        return

    target_srt_file = os.path.join(output_target_lang_dir, f"{media_name}_{target_lang.upper()}.srt")
    # check if output file already exists
    if os.path.exists(target_srt_file):
        print(f"Output file {target_srt_file} already exists")
        return

    # Translate the SRT file
    source_srt_content = read_srt(source_lang_srt_file)
    target_srt_content = translate_srt(source_srt_content, translation_config)

    with open(target_srt_file, 'w', encoding='utf-8') as file:
        file.write(target_srt_content)

    normalize_line_breaks(target_srt_file)

if __name__ == "__main__":
    main()