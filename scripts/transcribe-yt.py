import os
import sys
import yt_dlp
from dotenv import load_dotenv
import assemblyai as aai
import re

# Load enviroment variables from .env file
load_dotenv()

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

def main():
    # Check if URL was provided
    if len(sys.argv) not in [2, 3]:
        print("Usage: python download-audio.py <youtube-url> <target-lang>")
        sys.exit(1)
    
    url = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) == 3 else 'en'
    
    # Get script directory and construct path to content directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    content_dir = os.path.join(root_dir, "content")
    setup_directories(content_dir)

    output_dir = os.path.join(root_dir, "lang", lang)
    setup_directories(output_dir)
    
    file_path = download_audio(url, content_dir)
    
    file_name = os.path.basename(file_path)
    file_name = os.path.splitext(file_name)[0]

    if not file_path:
        print("Download failed.")
        return 1
    
    print(f"File path: {file_path}")

    output_srt_file = os.path.join(output_dir, f"{file_name}_{lang.upper()}.srt")

    if os.path.exists(output_srt_file):
        print(f"Output file {output_srt_file} already exists")
        return 1

    srt_content = transcribe(file_path)

    with open(output_srt_file, 'w', encoding='utf-8') as file:
        file.write(srt_content)
    
    print(f"Transcription saved to: {output_srt_file}")
    
    normalize_line_breaks(output_srt_file)

if __name__ == "__main__":
    main()