# CodePilot Local - GGUF Direct Evaluation via llama-cpp-python

import json
import time
from pathlib import Path
from tqdm import tqdm

try:
    from llama_cpp import Llama
except ImportError:
    print("Installing llama-cpp-python...")
    import subprocess
    subprocess.check_call(["pip", "install", "llama-cpp-python"])
    from llama_cpp import Llama

MODEL_PATH = "models/Qwen2.5-Coder-1.5B-Instruct.Q4_K_M.gguf"
TEST_FILE = "data/processed/test.jsonl"
OUTPUT_FILE = "results/finetuned_gguf_eval.json"

SYSTEM_PROMPT = "You are an expert Python code reviewer. Review the provided code snippet for security vulnerabilities, bugs, performance issues, error handling flaws, and resource leaks. Return ONLY valid JSON matching the required schema with line numbers, category, severity, issue description, and fix. Return only raw JSON string, NO markdown code blocks."

def load_data(file_path):
    rows = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def evaluate_gguf():
    p = Path(MODEL_PATH)
    if not p.exists():
        print(f"Error: Model file '{MODEL_PATH}' not found!")
        print("Please place 'Qwen2.5-Coder-1.5B-Instruct.Q4_K_M.gguf' inside the 'models/' directory.")
        return

    print(f"Loading GGUF model directly with llama-cpp: {MODEL_PATH}")
    llm = Llama(
        model_path=str(p),
        n_ctx=2048,
        n_threads=4,
        verbose=False
    )

    test_data = load_data(TEST_FILE)
    results = []
    valid_json_count = 0
    total_time = 0.0

    print(f"Evaluating {len(test_data)} test samples locally...")

    for row in tqdm(test_data, desc="Evaluating GGUF"):
        user_msg = row["messages"][-2]["content"]
        reference = row["messages"][-1]["content"]

        prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant\n"

        start = time.time()
        output = llm(
            prompt,
            max_tokens=256,
            temperature=0.1,
            top_p=0.95,
            stop=["<|im_end|>", "<|im_start|>"]
        )
        elapsed = time.time() - start
        total_time += elapsed

        raw_text = output["choices"][0]["text"].strip()

        # Clean markdown wrappers if present
        text = raw_text
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        is_valid = False
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "findings" in parsed:
                is_valid = True
                valid_json_count += 1
        except Exception:
             is_valid = False

        results.append({
            "prompt": user_msg,
            "reference": reference,
            "generated_output": raw_text,
            "cleaned_output": text,
            "is_json_valid": is_valid,
            "latency_seconds": elapsed
        })

    avg_latency = total_time / len(test_data) if test_data else 0
    valid_rate = (valid_json_count / len(test_data)) * 100 if test_data else 0

    print("\n" + "="*50)
    print("  Fine-Tuned GGUF Evaluation Summary")
    print("="*50)
    print(f"Total Samples:      {len(test_data)}")
    print(f"Valid JSON Rate:    {valid_json_count} / {len(test_data)} ({valid_rate:.1f}%)")
    print(f"Avg Latency/Review: {avg_latency:.2f} seconds")
    print("="*50)

    out_path = Path(OUTPUT_FILE)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Full evaluation results saved to {out_path.absolute()}")

if __name__ == "__main__":
    evaluate_gguf()
