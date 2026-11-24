import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm
from pathlib import Path

SYSTEM_PROMPT = "You are an expert Python code reviewer. Review the provided code snippet for security vulnerabilities, bugs, performance issues, error handling flaws, and resource leaks. Return ONLY valid JSON matching the required schema with line numbers, category, severity, issue description, and fix."
DEFAULT_MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

def read_jsonl(file_path):
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def generate_answer(model, tokenizer, messages, device):
    if isinstance(tokenizer.chat_template, str) and 'enable_thinking' in tokenizer.chat_template:
        if not tokenizer.chat_template.startswith('{% set enable_thinking = false %}'):
            tokenizer.chat_template = '{% set enable_thinking = false %}\n' + tokenizer.chat_template

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False
    )
    inputs = tokenizer(text, return_tensors='pt', add_special_tokens=False).to(device)
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(generated[0, inputs['input_ids'].shape[1]:], skip_special_tokens=True).strip()

def evaluate_model(model_name: str, model_id_or_path: str, eval_split_path: str, output_file: str):
    print(f"Loading {model_id_or_path} for evaluation...")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(model_id_or_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id_or_path,
        device_map="auto",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True
    )
    model.eval()

    eval_data = read_jsonl(eval_split_path)
    results = []

    print(f"Evaluating {len(eval_data)} samples on {device}...")
    for row in tqdm(eval_data, desc=f"Evaluating {model_name}"):
        user_messages = row["messages"][:-1]
        reference_output = row["messages"][-1]["content"]

        generated_output = generate_answer(model, tokenizer, user_messages, device)

        is_valid_json = False
        try:
            parsed = json.loads(generated_output)
            if isinstance(parsed, dict) and "findings" in parsed:
                is_valid_json = True
        except Exception:
            is_valid_json = False

        results.append({
            "prompt": user_messages[-1]["content"],
            "reference": reference_output,
            "generated_output": generated_output,
            "is_json_valid": is_valid_json
        })

    json_valid_count = sum(1 for r in results if r["is_json_valid"])
    valid_rate = (json_valid_count / len(results)) * 100 if results else 0

    print(f"\n--- Results for {model_name} ---")
    print(f"Total Evaluated: {len(results)}")
    print(f"Valid JSON Outputs: {json_valid_count} / {len(results)} ({valid_rate:.2f}%)")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results saved to {output_path.absolute()}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate a Qwen model on code review test split")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_ID, help="HF model ID or local path")
    parser.add_argument("--test-file", type=str, default="data/processed/test.jsonl", help="Path to test.jsonl")
    parser.add_argument("--output", type=str, default="results/baseline.json", help="Path to output results JSON")
    args = parser.parse_args()

    evaluate_model("Baseline (Untuned)", args.model, args.test_file, args.output)
