"""
Step 6B: Feedback-Aware Ranking Stress-Testing & Sensitivity Evaluation Engine.

Performs offline, deterministic evaluation of candidate ranking behavior across:
- Controlled stress-test scenarios (Quality vs Compatibility, Cold-Start, Tie-Breaking)
- Multi-point feedback weight sweeps: w in [0.00, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
- Multi-point Bayesian smoothing sweeps: m in [1, 5, 10, 20]
- Quantitative ranking-flip identification and threshold analysis
- Multi-tier cold-start shrinkage progression (n = 0, 1, 2, 5, 10, 20, 40, 50, 100)

All results are exported to JSON and CSV formats under evaluation/matching/results/.
"""
import os
import sys
import json
import csv
import math
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.services.feedback_score import calculate_feedback_signal, DEFAULT_SMOOTHING_M, DEFAULT_GLOBAL_PRIOR


WEIGHT_SWEEP = [0.00, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
SMOOTHING_SWEEP = [1.0, 5.0, 10.0, 20.0]
COLD_START_COUNTS = [0, 1, 2, 5, 10, 20, 30, 40, 50, 100]
EVAL_RATINGS = [5.0, 4.5, 4.0, 3.0, 2.0, 1.0]


def load_scenarios(scenarios_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Loads controlled benchmark scenarios from JSON."""
    if scenarios_path is None:
        scenarios_path = Path(__file__).resolve().parent / "feedback_scenarios.json"
    if not scenarios_path.exists():
        raise FileNotFoundError(f"Scenarios file not found: {scenarios_path}")
    with open(scenarios_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_candidate(
    candidate: Dict[str, Any],
    feedback_weight: float,
    smoothing_m: float = DEFAULT_SMOOTHING_M,
    global_prior: float = DEFAULT_GLOBAL_PRIOR,
) -> Dict[str, Any]:
    """Computes Bayesian feedback signal and experimental composite score for a candidate."""
    hybrid_score = float(candidate["hybrid_score"])
    raw_rating = candidate.get("rating")
    review_count = int(candidate.get("review_count", 0))

    fb_sig = calculate_feedback_signal(
        average_rating=raw_rating,
        review_count=review_count,
        smoothing_m=smoothing_m,
        global_prior=global_prior,
    )

    feedback_score = fb_sig["feedback_score"]
    w = max(0.0, min(1.0, float(feedback_weight)))
    experimental_score = ((1.0 - w) * hybrid_score) + (w * feedback_score)

    return {
        "tutor_id": candidate["tutor_id"],
        "name": candidate["name"],
        "hybrid_score": round(hybrid_score, 4),
        "raw_rating": raw_rating,
        "review_count": review_count,
        "adjusted_rating": fb_sig["adjusted_rating"],
        "feedback_score": fb_sig["feedback_score"],
        "feedback_confidence": fb_sig["confidence"],
        "has_reviews": fb_sig["has_reviews"],
        "feedback_weight": round(w, 2),
        "smoothing_m": round(smoothing_m, 1),
        "experimental_score": round(experimental_score, 6),
    }


def run_scenario(
    scenario: Dict[str, Any],
    feedback_weight: float,
    smoothing_m: float = DEFAULT_SMOOTHING_M,
    global_prior: float = DEFAULT_GLOBAL_PRIOR,
) -> List[Dict[str, Any]]:
    """Evaluates and ranks all candidates in a scenario under specified parameter settings."""
    evaluated = [
        evaluate_candidate(c, feedback_weight, smoothing_m, global_prior)
        for c in scenario["candidates"]
    ]
    # Deterministic sorting: higher experimental score, higher adjusted rating, stable tutor_id
    evaluated.sort(
        key=lambda x: (x["experimental_score"], x["adjusted_rating"], x["tutor_id"]),
        reverse=True,
    )
    for rank_idx, item in enumerate(evaluated, start=1):
        item["rank"] = rank_idx
        item["is_top_rank"] = rank_idx == 1
    return evaluated


def run_ranking_flip_analysis(
    scenarios: List[Dict[str, Any]],
    weights: List[float] = WEIGHT_SWEEP,
    smoothing_m: float = DEFAULT_SMOOTHING_M,
    global_prior: float = DEFAULT_GLOBAL_PRIOR,
) -> List[Dict[str, Any]]:
    """Analyzes whether feedback weighting causes rank changes relative to baseline (w=0.00)."""
    flip_records = []

    for sc in scenarios:
        sc_id = sc["scenario_id"]
        sc_title = sc["title"]

        # Run baseline (w=0.00)
        baseline_ranked = run_scenario(sc, feedback_weight=0.00, smoothing_m=smoothing_m, global_prior=global_prior)
        baseline_top = baseline_ranked[0]
        baseline_second = baseline_ranked[1] if len(baseline_ranked) > 1 else None
        baseline_score_diff = (
            round(baseline_top["experimental_score"] - baseline_second["experimental_score"], 6)
            if baseline_second
            else 0.0
        )

        for w in weights:
            exp_ranked = run_scenario(sc, feedback_weight=w, smoothing_m=smoothing_m, global_prior=global_prior)
            exp_top = exp_ranked[0]
            exp_second = exp_ranked[1] if len(exp_ranked) > 1 else None
            exp_score_diff = (
                round(exp_top["experimental_score"] - exp_second["experimental_score"], 6)
                if exp_second
                else 0.0
            )

            rank_flipped = exp_top["tutor_id"] != baseline_top["tutor_id"]

            flip_records.append({
                "scenario_id": sc_id,
                "scenario_title": sc_title,
                "feedback_weight": w,
                "smoothing_m": smoothing_m,
                "baseline_top_id": baseline_top["tutor_id"],
                "baseline_top_name": baseline_top["name"],
                "baseline_hybrid_score": baseline_top["hybrid_score"],
                "experimental_top_id": exp_top["tutor_id"],
                "experimental_top_name": exp_top["name"],
                "experimental_score": exp_top["experimental_score"],
                "rank_flipped": rank_flipped,
                "baseline_margin": baseline_score_diff,
                "experimental_margin": exp_score_diff,
            })

    return flip_records


def run_cold_start_analysis(
    counts: List[int] = COLD_START_COUNTS,
    ratings: List[float] = EVAL_RATINGS,
    smoothing_params: List[float] = SMOOTHING_SWEEP,
    global_prior: float = DEFAULT_GLOBAL_PRIOR,
) -> List[Dict[str, Any]]:
    """Generates detailed Bayesian shrinkage response curves across review volumes."""
    records = []
    for m in smoothing_params:
        for r in ratings:
            for n in counts:
                sig = calculate_feedback_signal(
                    average_rating=r if n > 0 else None,
                    review_count=n,
                    smoothing_m=m,
                    global_prior=global_prior,
                )
                raw_diff = abs(sig["adjusted_rating"] - r) if n > 0 else abs(sig["adjusted_rating"] - global_prior)
                records.append({
                    "review_count": n,
                    "raw_rating": r if n > 0 else "None (Cold Start)",
                    "smoothing_m": m,
                    "global_prior": global_prior,
                    "adjusted_rating": sig["adjusted_rating"],
                    "feedback_score": sig["feedback_score"],
                    "confidence": sig["confidence"],
                    "distance_from_raw": round(raw_diff, 4),
                    "has_reviews": sig["has_reviews"],
                })
    return records


def run_full_stress_test(
    scenarios_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Executes all stress-testing sweeps and exports output files."""
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    scenarios = load_scenarios(scenarios_path)

    # 1. Detailed candidate-level evaluations across (Scenario x Weight x Smoothing)
    all_scenario_evals = []
    for sc in scenarios:
        for m in SMOOTHING_SWEEP:
            for w in WEIGHT_SWEEP:
                ranked = run_scenario(sc, feedback_weight=w, smoothing_m=m)
                for item in ranked:
                    row = {
                        "scenario_id": sc["scenario_id"],
                        "scenario_title": sc["title"],
                        "category": sc["category"],
                        **item,
                    }
                    all_scenario_evals.append(row)

    # 2. Ranking flip analysis (across weights at default m=5.0)
    flip_records = run_ranking_flip_analysis(scenarios, weights=WEIGHT_SWEEP, smoothing_m=5.0)

    # 3. Cold start progression curves
    cold_start_records = run_cold_start_analysis()

    # 4. Sensitivity summary table
    sensitivity_summary = []
    for sc in scenarios:
        for w in WEIGHT_SWEEP:
            ranked = run_scenario(sc, feedback_weight=w, smoothing_m=5.0)
            top = ranked[0]
            second = ranked[1] if len(ranked) > 1 else None
            margin = round(top["experimental_score"] - second["experimental_score"], 6) if second else 0.0
            baseline_top_id = sc["candidates"][0]["tutor_id"] if sc["candidates"][0]["hybrid_score"] >= sc["candidates"][1]["hybrid_score"] else sc["candidates"][1]["tutor_id"]
            sensitivity_summary.append({
                "scenario_id": sc["scenario_id"],
                "scenario_title": sc["title"],
                "feedback_weight": f"{w:.2f}",
                "top_tutor_id": top["tutor_id"],
                "top_tutor_name": top["name"],
                "top_score": top["experimental_score"],
                "score_margin": margin,
                "rank_flipped": top["tutor_id"] != baseline_top_id,
            })

    # --- Export Files ---
    # 1. JSON
    json_path = output_dir / "feedback_scenario_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_scenarios": len(scenarios),
            "weight_sweep": WEIGHT_SWEEP,
            "smoothing_sweep": SMOOTHING_SWEEP,
            "detailed_evaluations": all_scenario_evals,
            "ranking_flips": flip_records,
            "sensitivity_summary": sensitivity_summary,
        }, f, indent=2)

    # 2. Scenario Results CSV
    csv_path = output_dir / "feedback_scenario_results.csv"
    if all_scenario_evals:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_scenario_evals[0].keys()))
            writer.writeheader()
            writer.writerows(all_scenario_evals)

    # 3. Ranking Flip CSV
    flip_csv_path = output_dir / "ranking_flip_analysis.csv"
    if flip_records:
        with open(flip_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(flip_records[0].keys()))
            writer.writeheader()
            writer.writerows(flip_records)

    # 4. Cold Start CSV
    cs_csv_path = output_dir / "cold_start_analysis.csv"
    if cold_start_records:
        with open(cs_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(cold_start_records[0].keys()))
            writer.writeheader()
            writer.writerows(cold_start_records)

    # 5. Sensitivity Summary CSV
    summary_csv_path = output_dir / "feedback_sensitivity_summary.csv"
    if sensitivity_summary:
        with open(summary_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(sensitivity_summary[0].keys()))
            writer.writeheader()
            writer.writerows(sensitivity_summary)

    return {
        "total_scenarios": len(scenarios),
        "total_candidate_evaluations": len(all_scenario_evals),
        "flip_records": flip_records,
        "sensitivity_summary": sensitivity_summary,
        "cold_start_records": cold_start_records,
    }


def main():
    parser = argparse.ArgumentParser(description="TutorLinkAI Step 6B Feedback Stress-Testing")
    args = parser.parse_args()

    print("=" * 80)
    print("TutorLinkAI — Step 6B: Feedback-Aware Ranking Stress-Test & Sensitivity Engine")
    print("=" * 80)

    results = run_full_stress_test()

    print(f"\nCompleted evaluation of {results['total_scenarios']} challenge scenarios across {len(WEIGHT_SWEEP)} weights and {len(SMOOTHING_SWEEP)} smoothing parameters.")
    print(f"Total candidate parameter evaluations: {results['total_candidate_evaluations']}\n")

    print("=" * 110)
    print("RANKING FLIP ANALYSIS (m = 5.0, Prior = 3.5)")
    print("=" * 110)
    print(f"{'Scenario':<42} | {'Weight':<6} | {'Top Tutor ID':<14} | {'Top Score':<10} | {'Margin':<8} | {'Flipped?'}")
    print("-" * 110)
    for row in results["sensitivity_summary"]:
        flip_badge = "[FLIP]" if row["rank_flipped"] else "No"
        print(
            f"{row['scenario_title'][:42]:<42} | "
            f"{row['feedback_weight']:<6} | "
            f"{row['top_tutor_id']:<14} | "
            f"{row['top_score']:<10.6f} | "
            f"{row['score_margin']:<8.6f} | "
            f"{flip_badge}"
        )
    print("-" * 110)

    print("\nResults exported to evaluation/matching/results/:")
    print("  - feedback_scenario_results.json")
    print("  - feedback_scenario_results.csv")
    print("  - ranking_flip_analysis.csv")
    print("  - cold_start_analysis.csv")
    print("  - feedback_sensitivity_summary.csv\n")


if __name__ == "__main__":
    main()
