import json
import pandas as pd
from pathlib import Path

def calculate_metrics(results):
    total_examples = len(results)
    if total_examples == 0: return {}

    json_valid_count = sum(1 for r in results if r["is_json_valid"])
    json_valid_rate = json_valid_count / total_examples

    # For this starter report, we will calculate a simple 'match rate' for findings
    # This needs to be expanded with Precision, Recall, F1 later as per plan Section 9.3
    # The 'matched_findings' field is currently a placeholder.

    # Placeholder for actual metric calculation (Precision, Recall, F1, Security recall, FP rate)
    # This part needs the 'match_finding_to_ground_truth' logic from the plan (Section 9.2)
    precision = "?"
    recall = "?"
    f1 = "?"
    security_recall = "?"
    fp_rate_clean = "?"

    return {
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "Security recall": security_recall,
        "FP rate (clean)": fp_rate_clean,
        "JSON valid": f"{json_valid_rate:.2f}",
        "Latency": "?",
        "RAM": "?"
    }

def make_report(baseline_path: Path, finetuned_path: Path | None = None, quantized_path: Path | None = None):
    baseline_results = json.loads(baseline_path.read_text())
    baseline_metrics = calculate_metrics(baseline_results)

    report_data = {
        "Model": [],
        "Precision": [],
        "Recall": [],
        "F1": [],
        "Security recall": [],
        "FP rate (clean)": [],
        "JSON valid": [],
        "Latency": [],
        "RAM": []
    }

    report_data["Model"].append("Base Qwen2.5-Coder-1.5B (untuned)")
    for k, v in baseline_metrics.items():
        report_data[k].append(v)

    if finetuned_path and finetuned_path.exists():
        finetuned_results = json.loads(finetuned_path.read_text())
        finetuned_metrics = calculate_metrics(finetuned_results)
        report_data["Model"].append("Fine-tuned (merged FP16)")
        for k, v in finetuned_metrics.items():
            report_data[k].append(v)

    if quantized_path and quantized_path.exists():
        quantized_results = json.loads(quantized_path.read_text())
        quantized_metrics = calculate_metrics(quantized_results)
        report_data["Model"].append("Fine-tuned Q4_K_M GGUF")
        for k, v in quantized_metrics.items():
            report_data[k].append(v)

    df = pd.DataFrame(report_data)

    report_md = "# CodePilot Local Evaluation Report\n\n"
    report_md += "## Quantitative Results\n\n"
    report_md += df.to_markdown(index=False)
    report_md += "\n\n**Note:** Precision, Recall, F1, Security recall, FP rate (clean), Latency, and RAM are placeholders (`?`) in this initial report. These metrics will be populated after implementing the full evaluation logic and local inference measurements as per the plan.\n"

    report_path = Path("results/REPORT.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md)
    print(f"Generated report: {report_path}")

if __name__ == "__main__":
    baseline_results_path = Path("results/baseline.json")
    # finetuned_results_path = Path("results/finetuned.json") # Uncomment when available
    # quantized_results_path = Path("results/quantized.json") # Uncomment when available

    make_report(baseline_results_path)
