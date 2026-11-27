# CodePilot Local - Real-world Code Review Dataset Downloader & Converter
# Downloads Python code review / vulnerability datasets from Hugging Face and prepares them.

import json
from datasets import load_dataset
from pathlib import Path
import random

OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "You are an expert Python code reviewer. Review the provided code snippet for "
    "security vulnerabilities, bugs, performance issues, error handling flaws, and "
    "resource leaks. Return ONLY valid JSON matching the required schema with line numbers, "
    "category, severity, issue description, and fix. Return only raw JSON string, NO markdown code blocks."
)

def format_code_with_line_numbers(code_str: str) -> str:
    lines = code_str.splitlines()
    return "\n".join([f"{i+1:3d} | {line}" for i, line in enumerate(lines)])

def download_and_process():
    print("Fetching real-world Python code review dataset from Hugging Face...")
    # Using 'bigcode/the-stack-smol-xs' or vulnerability / code review datasets
    try:
        # Load a standard real-world code security / review dataset
        ds = load_dataset("flawfinder/python-vulnerabilities", split="train")
        print(f"Loaded {len(ds)} real-world code review examples!")
    except Exception as e:
        print(f"Primary real-world dataset fetch failed ({e}), falling back to alternative real-world Python code dataset...")
        ds = load_dataset("bigcode/python-stack-vulnerabilities-sample", split="train")

    records = []
    for item in ds:
        code = item.get("code") or item.get("func") or item.get("content", "")
        if not code or len(code.splitlines()) > 50:  # Keep concise snippets suitable for 1.5B model
            continue

        findings = item.get("findings") or item.get("flaws", [])
        if not isinstance(findings, list):
            findings = []

        formatted_code = format_code_with_line_numbers(code)
        user_prompt = f"Review this Python code snippet:\n```python\n{formatted_code}\n```"
        assistant_response = json.dumps({"findings": findings}, ensure_ascii=False)

        records.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_response}
            ]
        })

    random.shuffle(records)
    n = len(records)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)

    train_data = records[:train_end]
    val_data = records[train_end:val_end]
    test_data = records[val_end:]

    def save_jsonl(data, filename):
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            for entry in data:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    save_jsonl(train_data, "train_real.jsonl")
    save_jsonl(val_data, "val_real.jsonl")
    save_jsonl(test_data, "test_real.jsonl")

    print(f"Done! Processed real dataset: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test samples saved to data/processed/")

if __name__ == "__main__":
    download_and_process()
