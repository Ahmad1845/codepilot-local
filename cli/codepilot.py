import sys
import os
import json
import urllib.request
import argparse
from pathlib import Path

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "codepilot-local"

SYSTEM_PROMPT = "You are an expert Python code reviewer. Review the provided code snippet for security vulnerabilities, bugs, performance issues, error handling flaws, and resource leaks. Return ONLY valid JSON matching the required schema with line numbers, category, severity, issue description, and fix. Return only raw JSON string, NO markdown code blocks."

def add_line_numbers(code_str: str) -> str:
    lines = code_str.splitlines()
    return "\n".join(f"{i+1:3d} | {line}" for i, line in enumerate(lines))

def clean_json_output(raw_output: str) -> str:
    """Removes markdown code block wrappers if present."""
    text = raw_output.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def query_ollama(prompt: str, model: str = MODEL_NAME) -> str:
    full_prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\nReview this Python code snippet:\n```python\n{prompt}\n```<|im_end|>\n<|im_start|>assistant\n"

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.95
        }
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_API_URL, data=data, headers={'Content-Type': 'application/json'})

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            return res_json.get("response", "")
    except Exception as e:
        print(f"Error connecting to Ollama at {OLLAMA_API_URL}: {e}", file=sys.stderr)
        print("Ensure Ollama is running (`ollama serve`) and model 'codepilot-local' is created (`ollama create codepilot-local -f export/Modelfile`).", file=sys.stderr)
        sys.exit(1)

def print_formatted_findings(findings_data, file_path):
    print("\n" + "="*70)
    print(f"  CodePilot Local Review — {file_path}")
    print("="*70)

    findings = findings_data.get("findings", [])
    if not findings:
        print("  ✅ Clean code! No issues detected.")
        print("="*70 + "\n")
        return

    print(f"  Found {len(findings)} issue(s):\n")
    for i, f in enumerate(findings, 1):
        line = f.get("line", "?")
        category = f.get("category", "general").upper()
        severity = f.get("severity", "medium").upper()
        issue = f.get("issue", f.get("issue_description", "Issue detected"))
        fix = f.get("fix", "No fix provided")

        print(f"  [{i}] Line {line} | [{severity}] {category}")
        print(f"      Issue: {issue}")
        print(f"      Fix:   {fix}")
        print("  " + "-"*65)
    print("="*70 + "\n")

def review_file(file_path: str, model_name: str, raw_json_flag: bool):
    p = Path(file_path)
    if not p.exists():
        print(f"Error: File '{file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    code_content = p.read_text(encoding="utf-8")
    formatted_code = add_line_numbers(code_content)

    raw_response = query_ollama(formatted_code, model=model_name)
    cleaned_response = clean_json_output(raw_response)

    try:
        parsed = json.loads(cleaned_response)
    except json.JSONDecodeError:
        print(f"Warning: Model output failed strict JSON parsing. Raw output:\n{raw_response}", file=sys.stderr)
        return

    if raw_json_flag:
        print(json.dumps(parsed, indent=2))
    else:
        print_formatted_findings(parsed, file_path)

def main():
    parser = argparse.ArgumentParser(description="CodePilot Local - AI Python Code Reviewer")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    review_parser = subparsers.add_parser("review", help="Review a Python file")
    review_parser.add_argument("file", type=str, help="Path to Python file to review")
    review_parser.add_argument("--model", type=str, default=MODEL_NAME, help="Ollama model name (default: codepilot-local)")
    review_parser.add_argument("--json", action="store_true", help="Output raw JSON format")

    args = parser.parse_args()

    if args.command == "review":
        review_file(args.file, args.model, args.json)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
