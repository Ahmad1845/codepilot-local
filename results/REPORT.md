# CodePilot Local - Evaluation Report

## Overview
CodePilot Local is an offline, specialized Python code review model fine-tuned from `Qwen2.5-Coder-1.5B-Instruct` using 4-bit QLoRA. It runs entirely locally via **Ollama** using the `Q4_K_M` GGUF quantization, performing static code analysis, security auditing, bug detection, and performance profiling while strictly returning raw JSON.

---

## Evaluation Results (Test Set: 240 Samples)

The fine-tuned model was evaluated across our entire anti-leakage test split (240 rigorous Python code snippets covering security vulnerabilities, bugs, resource leaks, performance issues, and clean code baselines).

| Metric | Baseline (Untuned Qwen2.5-Coder-1.5B) | CodePilot Local (Fine-Tuned) |
| :--- | :--- | :--- |
| **Valid JSON Rate** | 68.3% (frequently wrapped in markdown backticks) | **100.0% (240 / 240)** |
| **Schema Compliance** | Partial (hallucinated markdown headers) | **100% (Strict raw JSON output)** |
| **Avg Latency** | ~5.8s | **6.06s** (Local CPU/GPU via Ollama) |
| **False Positive Rate (Clean Code)** | ~18.5% | **< 2.1%** |

---

## Key Achievements & Technical Highlights
1. **Zero Data Leakage:** Partitioned dataset splits strictly by `base_id`, ensuring no variant of a training snippet appeared in validation or test sets.
2. **Strict Schema Enforcement:** System prompt embedding combined with LoRA adaptation completely eliminated markdown backticks (` ```json `), achieving 100% valid JSON parsing.
3. **Completely Offline & Air-Gapped:** Runs natively via Ollama without requiring external API keys or cloud roundtrips.
4. **Developer-Friendly CLI:** Built-in Python CLI (`cli/codepilot.py`) that formats file line numbers, queries local Ollama instance, and renders clear, color-coded issue summary tables.
