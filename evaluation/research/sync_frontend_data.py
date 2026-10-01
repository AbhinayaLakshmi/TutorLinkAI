import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

MATCHING_RESULTS_DIR = BASE_DIR / "evaluation" / "matching" / "results"
RESEARCH_RESULTS_DIR = BASE_DIR / "evaluation" / "research" / "results"
MATCHING_DIR = BASE_DIR / "evaluation" / "matching"
FRONTEND_DATA_DIR = BASE_DIR / "frontend" / "src" / "research" / "data"

from evaluation.matching.evaluate_feedback_scenarios import (
    load_scenarios,
    run_ranking_flip_analysis,
    run_cold_start_analysis,
    WEIGHT_SWEEP,
)


def sync_research_data() -> Path:
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Dataset summary
    with open(MATCHING_RESULTS_DIR / "dataset_summary.json", "r", encoding="utf-8") as f:
        dataset_summary = json.load(f)

    # 2. Model comparison
    with open(RESEARCH_RESULTS_DIR / "model_comparison.json", "r", encoding="utf-8") as f:
        model_comparison = json.load(f)

    # 3. Metric summary
    with open(RESEARCH_RESULTS_DIR / "metric_summary.json", "r", encoding="utf-8") as f:
        metric_summary = json.load(f)

    # 4. Manifest
    with open(RESEARCH_RESULTS_DIR / "evaluation_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 5. Queries, Tutors, Qrels
    with open(MATCHING_DIR / "queries.json", "r", encoding="utf-8") as f:
        queries = json.load(f)
    with open(MATCHING_DIR / "tutors.json", "r", encoding="utf-8") as f:
        tutors = json.load(f)
    with open(MATCHING_DIR / "qrels.json", "r", encoding="utf-8") as f:
        qrels = json.load(f)

    # 6. Scenarios & Flips
    scenarios = load_scenarios(MATCHING_DIR / "feedback_scenarios.json")
    ranking_flips = run_ranking_flip_analysis(scenarios, weights=WEIGHT_SWEEP, smoothing_m=5.0)

    # 7. Cold Start Progression
    cold_start_records = run_cold_start_analysis(
        counts=[0, 1, 2, 5, 10, 15, 20, 30, 40, 50],
        ratings=[5.0, 4.5, 4.0, 3.5, 3.0, 2.0],
        smoothing_params=[1.0, 5.0, 10.0, 20.0],
    )

    # 8. Limitations & Notices
    limitations = [
        {
            "category": "Controlled Synthetic Benchmark",
            "description": "The dataset contains 8 curated queries and 12 candidate tutors designed to rigorously isolate mathematical properties of dense semantic retrieval, topic overlap, and Bayesian shrinkage. It does not represent uncurated production logs or a generalized tutor population."
        },
        {
            "category": "Static Feedback Representation",
            "description": "Ratings and review counts represent static snapshots rather than sequential temporal event streams. User behavioral dynamics such as position bias and rating submission latency are not simulated."
        },
        {
            "category": "Offline Research Isolation",
            "description": "The feedback-aware scoring mechanism (Configuration E) is strictly an offline research experiment. The active production matching engine does not currently incorporate historical ratings into candidate ranking."
        },
        {
            "category": "Relevance Annotation Curated by Domain Standards",
            "description": "Ground truth relevance judgments were systematically assigned against formal CBSE/State Board and university curricula standards. Online user satisfaction may vary based on subjective interpersonal fit."
        }
    ]

    bundle = {
        "manifest": manifest,
        "dataset_summary": dataset_summary,
        "model_comparison": model_comparison,
        "metric_summary": metric_summary,
        "queries": queries,
        "tutors": tutors,
        "qrels": qrels,
        "scenarios": scenarios,
        "ranking_flips": ranking_flips,
        "cold_start": cold_start_records,
        "limitations": limitations,
    }

    output_path = FRONTEND_DATA_DIR / "researchData.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)

    print(f"Successfully synchronized research data to {output_path}")
    return output_path


if __name__ == "__main__":
    sync_research_data()
