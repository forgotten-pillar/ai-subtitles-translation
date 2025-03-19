import sys
import os
from dotenv import load_dotenv
import assemblyai as aai

# Load enviroment variables from .env file
load_dotenv()

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

    root_dir = os.path.dirname(os.path.abspath(__file__))
    media_name = os.path.basename(media_file)
    #without extension
    media_name = os.path.splitext(media_name)[0]
    
    output_dir = os.path.join(root_dir, "lang", lang)
    output_file = os.path.join(output_dir, f"{media_name}.srt")

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
    

if __name__ == "__main__":
    main()