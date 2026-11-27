# CodePilot Local - Full Test Set Evaluation via Local Ollama API

import json
import urllib.request
import time
from pathlib import Path
from tqdm import tqdm

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "codepilot-local"
TEST_FILE = "data/processed/test.jsonl"
OUTPUT_FILE = "results/finetuned_ollama_eval.json"

SYSTEM_PROMPT = "You are an expert Python code reviewer. Review the provided code snippet for security vulnerabilities, bugs, performance issues, error handling flaws, and resource leaks. Return ONLY valid JSON matching the required schema with line numbers, category, severity, issue description, and fix. Return only raw JSON string, NO markdown code blocks."

def load_data(file_path):
    rows = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def clean_json_output(raw_output: str) -> str:
    text = raw_output.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def query_ollama(prompt: str) -> str:
    full_prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.95
        }
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_API_URL, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        res_body = response.read().decode('utf-8')
        res_json = json.loads(res_body)
        return res_json.get("response", "")

def evaluate_ollama():
    test_data = load_data(TEST_FILE)
    results = []
    valid_json_count = 0
    total_time = 0.0

    print(f"Evaluating {len(test_data)} test samples via local Ollama ({MODEL_NAME})...")

    for row in tqdm(test_data, desc="Evaluating Ollama"):
        user_msg = row["messages"][-2]["content"]
        reference = row["messages"][-1]["content"]

        start = time.time()
        raw_text = query_ollama(user_msg)
        elapsed = time.time() - start
        total_time += elapsed

        cleaned_text = clean_json_output(raw_text)

        is_valid = False
        try:
            parsed = json.loads(cleaned_text)
            if isinstance(parsed, dict) and "findings" in parsed:
                is_valid = True
                valid_json_count += 1
        except Exception:
            is_valid = False

        results.append({
            "prompt": user_msg,
            "reference": reference,
            "generated_output": raw_text,
            "cleaned_output": cleaned_text,
            "is_json_valid": is_valid,
            "latency_seconds": elapsed
        })

    avg_latency = total_time / len(test_data) if test_data else 0
    valid_rate = (valid_json_count / len(test_data)) * 100 if test_data else 0

    print("\n" + "="*55)
    print("  CodePilot Local (Ollama Q4_K_M) Evaluation Summary")
    print("="*55)
    print(f"Total Test Samples:   {len(test_data)}")
    print(f"Valid JSON Rate:      {valid_json_count} / {len(test_data)} ({valid_rate:.1f}%)")
    print(f"Avg Latency/Review:   {avg_latency:.2f} seconds")
    print("="*55)

    out_path = Path(OUTPUT_FILE)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nFull evaluation results saved to {out_path.absolute()}")

if __name__ == "__main__":
    evaluate_ollama()
