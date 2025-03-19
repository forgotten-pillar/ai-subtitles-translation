import sys
import os
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

def setup_directories(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def transcribe(media_file):
    print(f"Transcribing {media_file}...")
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(media_file)

    srt_content = transcript.export_subtitles_srt()
    
    print("Transcription complete")

    return srt_content

def main():
    # python transcriebe.py [origin-media] [language]
    # [language] is optional, default is 'en'
    if(len(sys.argv) not in [2, 3]):
        print("Usage: python transcriebe.py [origin-media] [language]")
        return
    
    media_file = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) == 3 else 'en'

    # Determine the root directory (parent of the 'scripts' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))

    media_name = os.path.basename(media_file)
    #without extension
    media_name = os.path.splitext(media_name)[0]
    
    output_dir = os.path.join(root_dir, "lang", lang)
    setup_directories(output_dir)

    output_file = os.path.join(output_dir, f"{media_name}.srt")
    # check if output file already exists
    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists")
        return

    # check if media file exists
    if not os.path.exists(media_file):
        print(f"Media file {media_file} not found")
        return

    assembly_api_key = os.getenv("ASSEMBLY_AI_API_KEY")

    if assembly_api_key is None:
        print("Assembly AI API Key not found in .env file")
        return
    
    aai.settings.api_key = assembly_api_key

    srt_content = transcribe(media_file)
    
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(srt_content)

    normalize_line_breaks(output_file)
    

if __name__ == "__main__":
    main()