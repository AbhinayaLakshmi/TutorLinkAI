"""
Reproducible ML Recommendation Evaluation Pipeline Runner for TutorLinkAI.

Usage:
    python evaluation/research/run_all_evaluations.py

Steps performed:
1. Validates Step 7A benchmark dataset integrity.
2. Loads queries, tutors, qrels, and scenarios.
3. Evaluates all 5 recommendation configurations (A, B, C, D, E).
4. Computes Precision@K, Recall@5, MRR, NDCG@K, and Pairwise Accuracy.
5. Generates machine-readable output files in evaluation/research/results/:
   - model_comparison.json
   - model_comparison.csv
   - model_rankings.json
   - metric_summary.json
   - evaluation_manifest.json
6. Prints human-readable benchmark summary tables.
"""
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Any

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from evaluation.research.config import (
    ResearchConfig,
    RESULTS_DIR,
    ALL_MODELS,
    MODEL_DISPLAY_NAMES,
    PIPELINE_VERSION,
    DATASET_VERSION,
    METRICS_VERSION,
)
from evaluation.research.data_loader import BenchmarkDataLoader
from evaluation.research.evaluate import ResearchEvaluationEngine
from evaluation.matching.evaluate_feedback_scenarios import (
    run_ranking_flip_analysis,
    run_cold_start_analysis,
    WEIGHT_SWEEP,
    SMOOTHING_SWEEP,
)


def run_all_research_evaluations(
    feedback_weight: float = 0.10,
    smoothing_m: float = 5.0,
    global_prior: float = 3.5,
) -> Dict[str, Any]:
    """Executes the complete reproducible research evaluation pipeline."""
    print("=" * 100)
    print("TutorLinkAI — Step 7B: Reproducible ML Recommendation Evaluation Pipeline")
    print("=" * 100)

    # 1. Load and Validate Dataset
    print("\n[1/5] Loading and validating benchmark dataset...")
    loader = BenchmarkDataLoader(validate=True)
    dataset_summary = loader.get_dataset_summary()
    print(f"  - Queries: {dataset_summary['queries_count']}")
    print(f"  - Tutors: {dataset_summary['tutors_count']}")
    print(f"  - Qrels Queries: {dataset_summary['qrels_queries_count']}")
    print(f"  - Feedback Scenarios: {dataset_summary['feedback_scenarios_count']}")

    # 2. Initialize Evaluation Engine
    config = ResearchConfig(
        feedback_weight=feedback_weight,
        smoothing_m=smoothing_m,
        global_prior=global_prior,
    )
    engine = ResearchEvaluationEngine(config=config)

    # 3. Run All Model Configurations
    print("\n[2/5] Evaluating all 5 model configurations across all queries...")
    eval_results = engine.evaluate_dataset(
        queries=loader.queries,
        tutors=loader.tutors,
        qrels=loader.qrels,
    )

    ablation_summary = engine.build_ablation_summary(eval_results["aggregated_metrics"])

    # 4. Run Feedback & Cold-Start Analysis
    print("\n[3/5] Running Bayesian feedback stress-test and cold-start analyses...")
    ranking_flips = []
    cold_start_records = []
    if loader.feedback_scenarios:
        ranking_flips = run_ranking_flip_analysis(
            scenarios=loader.feedback_scenarios,
            weights=WEIGHT_SWEEP,
            smoothing_m=smoothing_m,
            global_prior=global_prior,
        )
        cold_start_records = run_cold_start_analysis(
            smoothing_params=[smoothing_m],
            global_prior=global_prior,
        )

    # 5. Export Results
    print("\n[4/5] Exporting machine-readable research artifacts...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # A. model_comparison.json
    comp_json_path = RESULTS_DIR / "model_comparison.json"
    with open(comp_json_path, "w", encoding="utf-8") as f:
        json.dump(ablation_summary, f, indent=2)

    # B. model_comparison.csv
    comp_csv_path = RESULTS_DIR / "model_comparison.csv"
    if ablation_summary:
        with open(comp_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(ablation_summary[0].keys()))
            writer.writeheader()
            writer.writerows(ablation_summary)

    # C. model_rankings.json
    rankings_json_path = RESULTS_DIR / "model_rankings.json"
    with open(rankings_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_results["model_rankings"], f, indent=2)

    # D. metric_summary.json
    metric_json_path = RESULTS_DIR / "metric_summary.json"
    with open(metric_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "config": config.to_dict(),
            "aggregated_metrics": eval_results["aggregated_metrics"],
            "per_query_metrics": eval_results["per_query_metrics"],
        }, f, indent=2)

    # E. evaluation_manifest.json
    manifest_path = RESULTS_DIR / "evaluation_manifest.json"
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "dataset_version": DATASET_VERSION,
        "metrics_version": METRICS_VERSION,
        "execution_parameters": config.to_dict(),
        "dataset_checksums": loader.get_checksums(),
        "models_evaluated": ALL_MODELS,
        "output_artifacts": {
            "model_comparison_json": str(comp_json_path.name),
            "model_comparison_csv": str(comp_csv_path.name),
            "model_rankings_json": str(rankings_json_path.name),
            "metric_summary_json": str(metric_json_path.name),
            "evaluation_manifest_json": str(manifest_path.name),
        },
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 6. Display Summary Table
    print("\n[5/5] Pipeline execution complete. Benchmark Summary:")
    print("=" * 115)
    header = f"{'Model Configuration':<52} | {'P@1':<6} | {'P@3':<6} | {'P@5':<6} | {'R@5':<6} | {'MRR':<6} | {'NDCG@3':<7} | {'NDCG@5':<7} | {'Pairwise':<8}"
    print(header)
    print("-" * 115)
    for row in ablation_summary:
        print(
            f"{row['display_name']:<52} | "
            f"{row['precision@1']:<6.4f} | "
            f"{row['precision@3']:<6.4f} | "
            f"{row['precision@5']:<6.4f} | "
            f"{row['recall@5']:<6.4f} | "
            f"{row['mrr']:<6.4f} | "
            f"{row['ndcg@3']:<7.4f} | "
            f"{row['ndcg@5']:<7.4f} | "
            f"{row['pairwise_accuracy']:<8.4f}"
        )
    print("=" * 115)
    print(f"\nArtifacts generated in: {RESULTS_DIR}")
    for k, v in manifest["output_artifacts"].items():
        print(f"  - {v}")
    print("=" * 100)

    return {
        "manifest": manifest,
        "eval_results": eval_results,
        "ablation_summary": ablation_summary,
        "ranking_flips": ranking_flips,
        "cold_start_records": cold_start_records,
    }


def main():
    run_all_research_evaluations()


if __name__ == "__main__":
    main()
