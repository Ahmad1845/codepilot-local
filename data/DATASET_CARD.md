# CodePilot Local Dataset Card

## Dataset Summary
The CodePilot Local dataset is a synthetic Python code review dataset designed for fine-tuning Qwen2.5-Coder models to identify security vulnerabilities, bugs, performance bottlenecks, error-handling flaws, and resource leaks in Python code.

## Split Statistics
- **Train**: 960 samples
- **Validation**: 180 samples
- **Test (Held-out)**: 240 samples

## Schema
Output assistant messages strictly conform to:
```json
{
  "findings": [
    {
      "line": 12,
      "category": "security|bug|performance|error-handling|resource-leak",
      "severity": "high|medium|low",
      "issue": "Description of defect",
      "fix": "Recommended fix"
    }
  ]
}
```

## Anti-Leakage Invariant
Splits are grouped strictly by base function ID. No base function or variant in `train` appears in `val` or `test`.

## License & Safety
All code snippets use permissively licensed patterns (Apache-2.0 / MIT style). No personal data or credentials are included.
