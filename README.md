# CodePilot Local: Enterprise-Grade Offline Python Code Reviewer

**Author:** Muhammad Ahmad  
**Hackathon Entry:** Qwen Local Hackathon 2026  
**Base Model:** `Qwen2.5-Coder-1.5B-Instruct`  
**Fine-Tuning Method:** 4-bit QLoRA (Unsloth & TRL `SFTTrainer`)  
**Quantization:** GGUF (`Q4_K_M`)  
**Inference Engine:** Ollama (100% Air-Gapped / Offline)  

---

## 🌟 Executive Summary

**CodePilot Local** is a specialized, open-weight Python code review model fine-tuned specifically to detect security vulnerabilities, logic bugs, performance bottlenecks, error handling flaws, and resource leaks. 

Unlike general-purpose coding assistants that often wrap JSON responses in markdown backticks (` ```json `) or introduce conversational chatter, CodePilot Local is rigorously trained on over **52,000 real-world code reviews** and custom synthetic datasets to output **strict, machine-parsable JSON** with exact line numbers and remediation steps. It operates entirely offline on local hardware via Ollama, ensuring zero data leakage and absolute privacy for proprietary codebases.

---

## 🛠️ System Architecture & Pipeline

```
[ Real-World Code Reviews (52K+) ] ──┐
                                     ├──> [ Anti-Leakage Dataset Partitioning ] ──> [ 4-bit QLoRA Training (Unsloth) ]
[ Synthetic Bug Injection (1.2K) ] ──┘                                                             │
                                                                                                   v
[ Ollama Local Engine ] <── [ GGUF Q4_K_M Conversion ] <── [ LoRA Adapter Merge & Export ] <───────┘
          │
          v
[ Developer CLI (cli/codepilot.py) ] ──> [ Structured JSON Findings & Pretty Tables ]
```

### 1. Data Engineering & Anti-Leakage Partitioning
- **Real-World Foundation:** Leveraged over 52,000 code review examples from `Dahoas/base_code_review` (StackExchange-derived discussions, code snippets, and peer reviews).
- **Synthetic Bug Injection:** Created synthetic pairs across 10 base Python patterns (SQL injection, hardcoded API keys, unclosed file descriptors, mutable default arguments, etc.) with explicit bug injection lambdas.
- **Anti-Leakage Split:** Partitioned splits strictly by `base_id`, guaranteeing that no variant of a training snippet leaked into validation or test sets.

### 2. Fine-Tuning & Prompt Engineering
- **Framework:** Trained using **Unsloth** and Hugging Face **TRL** `SFTTrainer` on Google Colab (T4/L4 GPU).
- **Hyperparameters:**
  - Rank ($r$): `16`
  - LoRA Alpha: `32`
  - Target Modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`
  - Learning Rate: `2e-4`
  - Batch Size: `2` (with gradient accumulation steps = `4`)
- **Strict JSON Enforcement:** The training system prompt explicitly instructs the model: *"Return ONLY valid JSON matching the required schema with line numbers, category, severity, issue description, and fix. Return only raw JSON string, NO markdown code blocks."*

### 3. Quantization & Local Execution
- **GGUF Export:** Merged LoRA adapters back into the 1.5B base model and quantized to `Q4_K_M` (~986 MB file size) for optimal memory footprint and speed.
- **Ollama Integration:** Configured a custom `Modelfile` specifying strict stop tokens (`<|im_start|>`, `<|im_end|>`) and low temperature (`0.1`) to eliminate hallucinations and formatting drift.

---

## 📊 Comprehensive Evaluation Results

Evaluated across a rigorous anti-leakage test set of **240 test samples**:

| Metric | Baseline (`Qwen2.5-Coder-1.5B-Instruct`) | CodePilot Local (Fine-Tuned) |
| :--- | :--- | :--- |
| **Valid JSON Rate** | 68.3% (frequently wrapped in markdown) | **100.0% (240 / 240)** |
| **Schema Compliance** | Partial (hallucinated markdown headers) | **100% (Strict raw JSON string)** |
| **Average Latency** | ~5.8s | **6.06s** (Local CPU/GPU inference) |
| **False Positive Rate** | ~18.5% on clean code | **< 2.1%** |

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally.

### Step 1: Set Up Ollama Model
Navigate to the models folder and create the local Ollama instance:
```bash
cd models
ollama create codepilot-local -f Modelfile
```

### Step 2: Run the Code Review CLI
Use the provided CLI wrapper to analyze any local Python file:
```bash
python cli/codepilot.py review demo/samples/vulnerable_sample.py
```

---

## 📂 Project Repository Structure

```tree
codepilot-local/
├── cli/
│   └── codepilot.py              # CLI wrapper (Ollama API REST client & JSON renderer)
├── data/
│   └── processed/                # Train, validation, and test jsonl datasets
├── models/
│   ├── Modelfile                 # Ollama runtime configuration & system prompt
│   └── codepilot-1.5b-adapter/   # Fine-tuned QLoRA adapter weights
├── results/
│   ├── REPORT.md                 # Detailed evaluation report
│   └── finetuned_ollama_eval.json# Full evaluation run metrics
├── scripts/
│   └── download_real_dataset.py  # Dataset downloader and formatter
├── notebooks/
│   └── train_real_dataset.ipynb  # Colab notebook for Unsloth fine-tuning
├── README.md                     # Project documentation
└── .gitignore
```

---

## 💡 Example CLI Output

When reviewing a vulnerable code snippet containing hardcoded secrets and SQL injection:
```bash
======================================================================
  CodePilot Local Review — demo/samples/vulnerable_sample.py
======================================================================
  Found 1 issue(s):

  [1] Line 8 | [HIGH] SECURITY
      Issue: SQL injection via parameter substitution with literal string input.
      Fix:   Use a parameterized query or escape input safely.
  -----------------------------------------------------------------
======================================================================
```

---
*Created by Muhammad Ahmad for the Qwen Local Hackathon 2026.*
