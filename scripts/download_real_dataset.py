# CodePilot Local - Real-world Code Review Dataset Downloader & Converter
# Downloads Dahoas/base_code_review from Hugging Face and formats StackExchange code/reviews.

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
    print("Fetching real-world Dahoas base_code_review dataset from Hugging Face...")
    ds = load_dataset("Dahoas/base_code_review", split="train")
    print(f"Loaded {len(ds)} real-world code review examples!")

    records = []
    for item in ds:
        body = item.get("body", "")
        answers = item.get("answers", [])

        if not body or not answers:
            continue

        # Extract code blocks from body if possible, or use body
        code_snippet = body[:800] # simplified snippet extraction
        review_text = answers[0].get("body", "Review and refactor code.") if answers else "Looks good."

        formatted_code = format_code_with_line_numbers(code_snippet)
        user_prompt = f"Review this code snippet:\n```\n{formatted_code}\n```"

        assistant_data = {
            "findings": [
                {
                    "line": 1,
                    "category": "code-review",
                    "severity": "medium",
                    "issue": review[:300] if 'review' in locals() else "Review required.",
                    "fix": "Apply recommended changes."
                }
            ]
        }
        assistant_response = json.dumps(assistant_data, ensure_ascii=False)

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
