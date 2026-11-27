# CodePilot Local 🚀

**CodePilot Local** is an offline, specialized Python code review model fine-tuned from `Qwen2.5-Coder-1.5B-Instruct` using 4-bit QLoRA. It detects security vulnerabilities, bugs, performance issues, error handling flaws, and resource leaks with line numbers, returning **strict valid JSON**. It runs 100% locally via **Ollama** (`Q4_K_M` GGUF quantization).

---

## Features
- **Offline & Private:** Powered by Ollama on your local machine.
- **Strict JSON Output:** Trained to omit markdown wrappers (` ```json `) for programmatic parsing.
- **Precise Line Numbering:** Pinpoints exact line numbers for each finding.
- **Developer CLI:** Simple command-line interface for reviewing local Python files.

---

## Quickstart

### 1. Requirements
- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally.

### 2. Setup Ollama Model
```bash
cd models
ollama create codepilot-local -f Modelfile
```

### 3. Run Code Review CLI
```bash
python cli/codepilot.py review path/to/script.py
```

---

## Evaluation Results
Tested on 240 rigorous test samples:
- **Valid JSON Rate:** **100.0%** (240 / 240)
- **Average Latency:** **6.06 seconds** per review
- **False Positive Rate:** < 2.1% on clean code

Read the full evaluation report in [`results/REPORT.md`](results/REPORT.md).

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
