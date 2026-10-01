import sys
import json
from pathlib import Path
import pytest

# Ensure project root and ai-service are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AI_SERVICE_DIR = BASE_DIR / "ai-service"
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from evaluation.research.config import (
    ResearchConfig,
    RESULTS_DIR,
    ALL_MODELS,
    MODEL_LEGACY_BASELINE,
    MODEL_DENSE_SEMANTIC,
    MODEL_TOPIC_OVERLAP,
    MODEL_FULL_HYBRID,
    MODEL_FULL_HYBRID_FEEDBACK,
    MODEL_COMPONENTS,
    PROD_WEIGHT_LEARNING_NEED,
    PROD_WEIGHT_LOCATION,
    PROD_WEIGHT_FEE,
    PROD_WEIGHT_TIME,
)
from evaluation.research.data_loader import BenchmarkDataLoader
from evaluation.research.models import ResearchModelsEvaluator
from evaluation.research.evaluate import ResearchEvaluationEngine
from evaluation.research.metrics import (
    compute_precision_at_k,
    compute_recall_at_k,
    compute_mrr,
    compute_ndcg_at_k,
    compute_pairwise_ranking_accuracy,
    compute_all_metrics,
)
from evaluation.research.run_all_evaluations import run_all_research_evaluations
from app.matching.config import (
    DEFAULT_WEIGHT_LEARNING_NEED,
    DEFAULT_WEIGHT_LOCATION,
    DEFAULT_WEIGHT_FEE,
    DEFAULT_WEIGHT_TIME,
)


def test_research_dataset_loader():
    loader = BenchmarkDataLoader(validate=True)
    summary = loader.get_dataset_summary()
    assert summary["queries_count"] == 8
    assert summary["tutors_count"] == 12
    assert summary["qrels_queries_count"] == 8
    assert len(loader.get_checksums()) >= 3


def test_all_model_configurations_exist():
    assert len(ALL_MODELS) == 5
    assert MODEL_LEGACY_BASELINE in ALL_MODELS
    assert MODEL_DENSE_SEMANTIC in ALL_MODELS
    assert MODEL_TOPIC_OVERLAP in ALL_MODELS
    assert MODEL_FULL_HYBRID in ALL_MODELS
    assert MODEL_FULL_HYBRID_FEEDBACK in ALL_MODELS

    for m in ALL_MODELS:
        assert m in MODEL_COMPONENTS


def test_metrics_determinism_and_bounds():
    ranked_ids = ["t1", "t2", "t3", "t4", "t5"]
    qrels = {"t1": 3, "t2": 2, "t3": 1, "t4": 0, "t5": 0}

    p1 = compute_precision_at_k(ranked_ids, qrels, k=1)
    p3 = compute_precision_at_k(ranked_ids, qrels, k=3)
    r5 = compute_recall_at_k(ranked_ids, qrels, k=5)
    mrr = compute_mrr(ranked_ids, qrels)
    ndcg3 = compute_ndcg_at_k(ranked_ids, qrels, k=3)
    ndcg5 = compute_ndcg_at_k(ranked_ids, qrels, k=5)

    ranked_items = [{"id": tid, "overall_score": 1.0 - (idx * 0.1)} for idx, tid in enumerate(ranked_ids)]
    pw_acc = compute_pairwise_ranking_accuracy(ranked_items, qrels)

    for metric_val in [p1, p3, r5, mrr, ndcg3, ndcg5, pw_acc]:
        assert 0.0 <= metric_val <= 1.0

    assert p1 == 1.0
    assert p3 == pytest.approx(2.0 / 3.0, abs=1e-4)
    assert r5 == 1.0
    assert mrr == 1.0
    assert pw_acc == 1.0


def test_legacy_baseline_configuration_invariants():
    loader = BenchmarkDataLoader(validate=False)
    evaluator = ResearchModelsEvaluator()

    q = loader.queries[0]
    legacy_ranked = evaluator.run_legacy_baseline(q, loader.tutors)

    assert len(legacy_ranked) > 0
    for cand in legacy_ranked:
        assert cand["learning_need_score"] == 1.0
        assert "overall_score" in cand
        assert cand["model_configuration"] == MODEL_LEGACY_BASELINE


def test_full_hybrid_production_formulation():
    loader = BenchmarkDataLoader(validate=False)
    evaluator = ResearchModelsEvaluator()

    q = loader.queries[0]
    hybrid_ranked = evaluator.run_full_hybrid(q, loader.tutors)

    assert len(hybrid_ranked) > 0
    for cand in hybrid_ranked:
        assert "semantic_score" in cand
        assert "topic_score" in cand
        assert "learning_need_score" in cand
        assert cand["model_configuration"] == MODEL_FULL_HYBRID


def test_feedback_configuration_remains_experimental():
    loader = BenchmarkDataLoader(validate=False)
    evaluator = ResearchModelsEvaluator()

    q = loader.queries[0]
    feedback_ranked = evaluator.run_full_hybrid_feedback(
        q, loader.tutors, feedback_weight=0.10, smoothing_m=5.0
    )

    assert len(feedback_ranked) > 0
    for cand in feedback_ranked:
        assert "hybrid_base_score" in cand
        assert "feedback_score" in cand
        assert "adjusted_rating" in cand
        assert "feedback_confidence" in cand
        assert cand["feedback_weight"] == 0.10
        assert cand["model_configuration"] == MODEL_FULL_HYBRID_FEEDBACK


def test_evaluation_runner_generates_manifest_and_artifacts():
    results = run_all_research_evaluations(feedback_weight=0.10, smoothing_m=5.0)

    assert "manifest" in results
    assert "ablation_summary" in results
    assert len(results["ablation_summary"]) == 5

    manifest_file = RESULTS_DIR / "evaluation_manifest.json"
    comp_json_file = RESULTS_DIR / "model_comparison.json"
    comp_csv_file = RESULTS_DIR / "model_comparison.csv"
    rankings_file = RESULTS_DIR / "model_rankings.json"
    metric_file = RESULTS_DIR / "metric_summary.json"

    assert manifest_file.exists()
    assert comp_json_file.exists()
    assert comp_csv_file.exists()
    assert rankings_file.exists()
    assert metric_file.exists()


def test_repeated_runs_produce_equivalent_results():
    loader = BenchmarkDataLoader(validate=False)
    engine = ResearchEvaluationEngine(config=ResearchConfig())

    res1 = engine.evaluate_dataset(loader.queries, loader.tutors, loader.qrels)
    res2 = engine.evaluate_dataset(loader.queries, loader.tutors, loader.qrels)

    assert res1["aggregated_metrics"] == res2["aggregated_metrics"]


def test_production_matching_weights_remain_unmodified():
    # Strict invariant verification
    assert DEFAULT_WEIGHT_LEARNING_NEED == PROD_WEIGHT_LEARNING_NEED == 0.45
    assert DEFAULT_WEIGHT_LOCATION == PROD_WEIGHT_LOCATION == 0.20
    assert DEFAULT_WEIGHT_FEE == PROD_WEIGHT_FEE == 0.20
    assert DEFAULT_WEIGHT_TIME == PROD_WEIGHT_TIME == 0.15
