import os
import subprocess
import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm

# --- CONFIGURATION ---
MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
TEST_FILE = "data/processed/test.jsonl"
OUTPUT_FILE = "results/baseline.json"

# --- HELPER FUNCTIONS ---
def install_dependencies():
    print("Installing dependencies...")
    subprocess.check_call(["pip", "install", "-q", "transformers", "accelerate", "bitsandbytes", "sentencepiece", "protobuf", "datasets", "tqdm", "torch"])
    print("Dependencies installed.")

def load_data(file_path):
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def generate_answer(model, tokenizer, messages, device):
    # Ensure consistent prompt format
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

def run_evaluation():
    # 1. Install Dependencies
    install_dependencies()

    # 2. Load Model & Tokenizer
    print(f"Loading {MODEL_ID} for evaluation...")
    device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map="auto",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True
    )
    model.eval()

    # 3. Load Test Data
    eval_data = load_data(TEST_FILE)
    results = []

    # 4. Evaluate
    print(f"Evaluating {len(eval_data)} samples on {device}...")
    for row in tqdm(eval_data, desc="Evaluating"):
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

    # 5. Save Results
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nEvaluation complete. Results saved to {output_path.absolute()}")

if __name__ == "__main__":
    run_evaluation()
