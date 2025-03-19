import sys
import os
from dotenv import load_dotenv
import yaml
import re
from anthropic import Anthropic

# Load enviroment variables from .env file
load_dotenv()

def split_srt_into_batches(srt_content, batch_size=200):
    srt_content = srt_content.strip()
    subtitles = re.split(r'\n(?=\d+\n\d{2}:\d{2}:\d{2},\d{3} -->)', srt_content)
    batches = [subtitles[i:i + batch_size] for i in range(0, len(subtitles), batch_size)]
    return ["\n".join(batch) + "\n" for batch in batches]

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

def read_srt(srt_file):
    with open(srt_file, 'r', encoding='utf-8') as file:
        srt_content = file.read()
    return srt_content

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
    # python translate-srt.py [origin-srt] [target-lang]
    if(len(sys.argv) != 3):
        print("Usage: python translate-srt.py [origin-srt] [target-lang]")
        return
    
    origin_srt_file = sys.argv[1]
    # check if it finishes with .srt if not add it
    if not origin_srt_file.endswith('.srt'):
        origin_srt_file += '.srt'
    
    target_lang = sys.argv[2]

    # Determine the root directory (parent of the 'scripts' folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))

    srt_source_file = os.path.join(root_dir, "lang", "en", origin_srt_file)
    # check if media file exists
    if not os.path.exists(srt_source_file):
        print(f"Media file {srt_source_file} not found")
        return
    
    normalize_line_breaks(srt_source_file)

    # get media name without extension
    media_name = os.path.splitext(origin_srt_file)[0]

    output_dir = os.path.join(root_dir, "lang", target_lang)
    setup_directories(output_dir)

    output_file = os.path.join(output_dir, f"{media_name}_{target_lang.upper()}.srt")
    # check if output file already exists
    if os.path.exists(output_file):
        print(f"Output file {output_file} already exists")
        return
    
    # load translation configuration
    translation_config = os.path.join(root_dir, "lang", target_lang, "config.yaml")
    if not os.path.exists(translation_config):
        print(f"Translation configuration file {translation_config} not found")
        return

    srt_content = read_srt(srt_source_file)
    srt_translated = translate_srt(srt_content, translation_config)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(srt_translated)

    normalize_line_breaks(output_file)

if __name__ == "__main__":
    main()