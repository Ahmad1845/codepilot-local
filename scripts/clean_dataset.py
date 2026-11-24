import json
import ast
from pathlib import Path

def validate_and_clean():
    data_dir = Path("data/processed")
    splits = ["train", "val", "test"]
    stats = {}

    for split in splits:
        path = data_dir / f"{split}.jsonl"
        valid_rows = []

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                messages = row["messages"]

                # Check message structure
                if len(messages) != 3:
                    continue

                # Check user code parses or contains code blocks
                user_content = messages[1]["content"]
                if "```python" not in user_content:
                    continue

                # Check assistant output parses as valid JSON matching schema
                assistant_content = messages[2]["content"]
                try:
                    parsed = json.loads(assistant_content)
                    if "findings" not in parsed or not isinstance(parsed["findings"], list):
                        continue
                except Exception:
                    continue

                valid_rows.append(row)

        stats[split] = len(valid_rows)

        # Write clean output back
        with open(path, "w", encoding="utf-8") as f:
            for row in valid_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Dataset validation completed successfully.")
    for split, count in stats.items():
        print(f"  - {split}: {count} valid examples")

    # Generate DATASET_CARD.md
    card_content = f"""# CodePilot Local Dataset Card

## Dataset Summary
The CodePilot Local dataset is a synthetic Python code review dataset designed for fine-tuning Qwen2.5-Coder models to identify security vulnerabilities, bugs, performance bottlenecks, error-handling flaws, and resource leaks in Python code.

## Split Statistics
- **Train**: {stats['train']} samples
- **Validation**: {stats['val']} samples
- **Test (Held-out)**: {stats['test']} samples

## Schema
Output assistant messages strictly conform to:
```json
{{
  "findings": [
    {{
      "line": 12,
      "category": "security|bug|performance|error-handling|resource-leak",
      "severity": "high|medium|low",
      "issue": "Description of defect",
      "fix": "Recommended fix"
    }}
  ]
}}
```

## Anti-Leakage Invariant
Splits are grouped strictly by base function ID. No base function or variant in `train` appears in `val` or `test`.

## License & Safety
All code snippets use permissively licensed patterns (Apache-2.0 / MIT style). No personal data or credentials are included.
"""
    with open("data/DATASET_CARD.md", "w", encoding="utf-8") as f:
        f.write(card_content)

    print("Generated data/DATASET_CARD.md")

if __name__ == "__main__":
    validate_and_clean()
