import os

def write_common_py_file(content):
    os.makedirs('scripts', exist_ok=True)
    with open('scripts/common.py', 'w', encoding='utf-8') as f:
        f.write(content)

# Content for common.py
common_content = '''
import json

def read_rows(file_path):
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():  # Only process non-empty lines
                rows.append(json.loads(line))
    return rows

def cell(text):
    # Helper to clean text for markdown tables
    return str(text).replace('|', '\\|').replace('\n', '<br>')
'''

write_common_py_file(common_content)
