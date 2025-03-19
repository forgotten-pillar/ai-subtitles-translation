import re
import sys

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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py path/to/file.srt")
    else:
        normalize_line_breaks(sys.argv[1])