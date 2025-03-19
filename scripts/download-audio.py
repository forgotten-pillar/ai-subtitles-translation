#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import yt_dlp

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
        bool: True if downloaded, False if skipped
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
            return False
        elif os.path.exists(webm_path):
            print(f"File already exists as WebM: {webm_path}")
            print("Skipping download...")
            return False
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
            return True
    except Exception as e:
        print(f"Error downloading audio: {str(e)}")
        sys.exit(1)

def main():
    # Check if URL was provided
    if len(sys.argv) < 2:
        print("Usage: python download-audio.py <youtube-url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Get script directory and construct path to content directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    content_dir = os.path.join(root_dir, "content")
    
    download_audio(url, content_dir)

if __name__ == "__main__":
    main()