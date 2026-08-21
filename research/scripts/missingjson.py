import os
import re
import json

FOLDER_PATH = '/ssd1/tuannw/infer_result/28-05-25'
MISSING_TXT_PATH = '/ssd1/tuannw/infer_result/28-05-25/expected.txt'
OUTPUT_JSON_PATH = '/ssd1/tuannw/meta.json'

SUB_FOLDER = re.compile(r'^[A-Z]{2} - \d{3}$')

def create_missing_json(FOLDER_PATH, missing_txt_path, output_json_path):
    # Get sorted list of subfolders matching the pattern
    subfolders = sorted(
        [entry for entry in os.listdir(FOLDER_PATH)
         if os.path.isdir(os.path.join(FOLDER_PATH, entry)) and SUB_FOLDER.match(entry)]
    )

    # Read expected.txt lines
    with open(missing_txt_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) != len(subfolders):
        raise ValueError("Number of lines in expected.txt does not match number of subfolders.")

    # Load existing data if file exists
    if os.path.exists(output_json_path):
        with open(output_json_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    # Add or update entries
    for subfolder, line in zip(subfolders, lines):
        missing = line == '0'
        key = os.path.join(FOLDER_PATH, subfolder)
        data[key] = {"missing": missing}

    with open(output_json_path, 'w') as f:
        json.dump(data, f, indent=4)

create_missing_json(FOLDER_PATH, MISSING_TXT_PATH, OUTPUT_JSON_PATH)
