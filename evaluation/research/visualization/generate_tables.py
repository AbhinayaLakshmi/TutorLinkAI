"""
Publication Table Generator for TutorLinkAI Research Evaluation.
Converts benchmark evaluation outputs into formatted CSV and Markdown tables.
"""
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from evaluation.research.config import (
    RESULTS_DIR,
    FEEDBACK_SCENARIOS_PATH,
    ALL_MODELS,
    MODEL_DISPLAY_NAMES,
)
from evaluation.matching.evaluate_feedback_scenarios import (
    load_scenarios,
    run_ranking_flip_analysis,
    run_cold_start_analysis,
    WEIGHT_SWEEP,
)

TABLES_DIR = RESULTS_DIR / "tables"


def generate_model_comparison_table() -> Tuple[Path, Path]:
    """Generates model_comparison.csv and model_comparison.md."""
    comp_json_path = RESULTS_DIR / "model_comparison.json"
    if not comp_json_path.exists():
        # Fallback to run evaluation if missing
        from evaluation.research.run_all_evaluations import run_all_research_evaluations
        run_all_research_evaluations()

    with open(comp_json_path, "r", encoding="utf-8") as f:
        model_rows = json.load(f)

    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. CSV Export
    csv_path = TABLES_DIR / "model_comparison.csv"
    if model_rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(model_rows[0].keys()))
            writer.writeheader()
            writer.writerows(model_rows)

    # 2. Markdown Export
    md_path = TABLES_DIR / "model_comparison.md"
    md_lines = [
        "# Model Comparison & Component Ablation Table",
        "",
        "| Configuration | Model ID | Semantic | Topic | Constraints | Feedback | P@1 | P@3 | P@5 | R@5 | MRR | NDCG@3 | NDCG@5 | Pairwise Acc |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for row in model_rows:
        sem_icon = "✓" if row.get("semantic_embeddings") else "✗"
        top_icon = "✓" if row.get("topic_overlap") else "✗"
        con_icon = "✓" if row.get("location_scoring") else "✗"
        fb_icon = f"✓ (w={row.get('feedback_weight'):.2f})" if row.get("bayesian_feedback") else "✗"

        line = (
            f"| **{row['display_name']}** | `{row['model_id']}` | "
            f"{sem_icon} | {top_icon} | {con_icon} | {fb_icon} | "
            f"`{row['precision@1']:.4f}` | `{row['precision@3']:.4f}` | `{row['precision@5']:.4f}` | "
            f"`{row['recall@5']:.4f}` | `{row['mrr']:.4f}` | `{row['ndcg@3']:.4f}` | `{row['ndcg@5']:.4f}` | "
            f"`{row['pairwise_accuracy']:.4f}` |"
        )
        md_lines.append(line)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    return csv_path, md_path


def generate_ranking_flip_table() -> Tuple[Path, Path]:
    """Generates ranking_flip_table.csv and ranking_flip_table.md across challenge scenarios."""
    scenarios = load_scenarios(FEEDBACK_SCENARIOS_PATH)
    flip_records = run_ranking_flip_analysis(scenarios, weights=WEIGHT_SWEEP, smoothing_m=5.0)

    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. CSV Export
    csv_path = TABLES_DIR / "ranking_flip_table.csv"
    if flip_records:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(flip_records[0].keys()))
            writer.writeheader()
            writer.writerows(flip_records)

    # 2. Markdown Export
    md_path = TABLES_DIR / "ranking_flip_table.md"
    md_lines = [
        "# Ranking Flip Sensitivity Analysis Table ($m=5.0, \\mu=3.5$)",
        "",
        "| Scenario | Weight ($w$) | Baseline Top Tutor | Feedback Top Tutor | Base Margin | Exp Margin | Flipped? |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :---: |",
    ]

    for r in flip_records:
        flip_badge = "**YES [FLIP]**" if r["rank_flipped"] else "No"
        line = (
            f"| {r['scenario_title']} | `{r['feedback_weight']:.2f}` | "
            f"{r['baseline_top_name']} (`{r['baseline_top_id']}`) | "
            f"{r['experimental_top_name']} (`{r['experimental_top_id']}`) | "
            f"`+{r['baseline_margin']:.4f}` | `+{r['experimental_margin']:.4f}` | {flip_badge} |"
        )
        md_lines.append(line)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    return csv_path, md_path


def generate_cold_start_table() -> Tuple[Path, Path]:
    """Generates cold_start_table.csv and cold_start_table.md."""
    records = run_cold_start_analysis(
        counts=[0, 1, 5, 10, 20, 40],
        ratings=[5.0, 4.0, 3.0],
        smoothing_params=[1.0, 5.0, 10.0, 20.0],
    )

    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. CSV Export
    csv_path = TABLES_DIR / "cold_start_table.csv"
    if records:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)

    # 2. Markdown Export (Filtered at default m=5.0 for clean presentation)
    md_path = TABLES_DIR / "cold_start_table.md"
    md_lines = [
        "# Bayesian Cold-Start Shrinkage Table (Default $m=5.0, \\mu=3.5$)",
        "",
        "| Review Count ($n$) | Raw Rating ($\\overline{r}$) | Adjusted Rating ($r_{\\text{adj}}$) | Normalized Score ($S$) | Confidence ($C$) | Shrinkage Distance $|\\overline{r} - r_{\\text{adj}}|$ |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in records:
        if r["smoothing_m"] == 5.0 and (r["raw_rating"] == 5.0 or r["review_count"] == 0):
            raw_str = f"{r['raw_rating']:.1f}★" if isinstance(r['raw_rating'], (int, float)) else "None (Prior)"
            line = (
                f"| **{r['review_count']} reviews** | {raw_str} | "
                f"`{r['adjusted_rating']:.4f}` | `{r['feedback_score']:.4f}` | "
                f"`{r['confidence']:.4f}` | `{r['distance_from_raw']:.4f}` |"
            )
            md_lines.append(line)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    return csv_path, md_path


def generate_all_tables() -> Dict[str, Path]:
    """Generates all CSV and Markdown publication tables."""
    print("Generating publication tables in evaluation/research/results/tables/...")
    comp_csv, comp_md = generate_model_comparison_table()
    flip_csv, flip_md = generate_ranking_flip_table()
    cold_csv, cold_md = generate_cold_start_table()

    outputs = {
        "model_comparison_csv": comp_csv,
        "model_comparison_md": comp_md,
        "ranking_flip_csv": flip_csv,
        "ranking_flip_md": flip_md,
        "cold_start_csv": cold_csv,
        "cold_start_md": cold_md,
    }

    for name, path in outputs.items():
        print(f"  - {path.name}")

    return outputs


def main():
    generate_all_tables()


if __name__ == "__main__":
    main()
