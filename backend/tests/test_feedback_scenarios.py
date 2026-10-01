import sys
from pathlib import Path
import pytest

# Ensure ai-service and project root are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AI_SERVICE_DIR = BASE_DIR / "ai-service"
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.services.feedback_score import calculate_feedback_signal
from app.matching.config import (
    DEFAULT_WEIGHT_LEARNING_NEED,
    DEFAULT_WEIGHT_SUBJECT,
    DEFAULT_WEIGHT_LOCATION,
    DEFAULT_WEIGHT_FEE,
    DEFAULT_WEIGHT_TIME,
)
from evaluation.matching.evaluate_feedback_scenarios import (
    load_scenarios,
    evaluate_candidate,
    run_scenario,
    run_ranking_flip_analysis,
    run_cold_start_analysis,
    WEIGHT_SWEEP,
    SMOOTHING_SWEEP,
)


def test_scenario_dataset_loads_correctly():
    scenarios = load_scenarios()
    assert isinstance(scenarios, list)
    assert len(scenarios) == 6


def test_all_required_scenarios_exist():
    scenarios = load_scenarios()
    scenario_ids = [sc["scenario_id"] for sc in scenarios]

    required_ids = [
        "scenario_1_quality_vs_compatibility",
        "scenario_2_cold_start_vs_established",
        "scenario_3_new_tutor_no_reviews",
        "scenario_4_strong_compat_vs_strong_feedback",
        "scenario_5_similar_compat_different_feedback",
        "scenario_6_same_rating_different_evidence",
    ]

    for req_id in required_ids:
        assert req_id in scenario_ids
        sc = next(s for s in scenarios if s["scenario_id"] == req_id)
        assert len(sc["candidates"]) >= 2
        for cand in sc["candidates"]:
            assert "hybrid_score" in cand
            assert "review_count" in cand


def test_bayesian_shrinkage_is_deterministic():
    sig1 = calculate_feedback_signal(4.8, 30, smoothing_m=5.0, global_prior=3.5)
    sig2 = calculate_feedback_signal(4.8, 30, smoothing_m=5.0, global_prior=3.5)
    assert sig1 == sig2
    assert sig1["adjusted_rating"] == pytest.approx((30 / 35) * 4.8 + (5 / 35) * 3.5, abs=1e-4)


def test_zero_review_behavior():
    sig = calculate_feedback_signal(None, 0, smoothing_m=5.0, global_prior=3.5)
    assert sig["has_reviews"] is False
    assert sig["confidence"] == 0.0
    assert sig["adjusted_rating"] == 3.5
    assert sig["feedback_score"] == pytest.approx(0.625, abs=1e-4)


def test_one_review_shrunk_toward_prior():
    # With m=5, 1 review gets weight 1/6 (16.7%) and prior gets 5/6 (83.3%)
    sig = calculate_feedback_signal(5.0, 1, smoothing_m=5.0, global_prior=3.5)
    assert sig["confidence"] == pytest.approx(1.0 / 6.0, abs=1e-4)
    assert sig["adjusted_rating"] == pytest.approx((1 / 6) * 5.0 + (5 / 6) * 3.5, abs=1e-4)
    # Distance from raw 5.0 is substantial
    assert abs(sig["adjusted_rating"] - 5.0) > 1.20


def test_increasing_review_count_increases_evidence_confidence():
    counts = [0, 1, 2, 5, 10, 20, 40, 50, 100]
    confidences = [
        calculate_feedback_signal(4.8, c, smoothing_m=5.0, global_prior=3.5)["confidence"]
        for c in counts
    ]
    for i in range(len(confidences) - 1):
        assert confidences[i] < confidences[i + 1]
    assert confidences[-1] < 1.0


def test_smoothing_parameter_changes_adjusted_ratings():
    # With smaller m=1, single 5.0 rating gets 50% weight -> adj = 4.25
    sig_m1 = calculate_feedback_signal(5.0, 1, smoothing_m=1.0, global_prior=3.5)
    # With larger m=20, single 5.0 rating gets 1/21 weight -> adj = 3.5714
    sig_m20 = calculate_feedback_signal(5.0, 1, smoothing_m=20.0, global_prior=3.5)

    assert sig_m1["adjusted_rating"] > sig_m20["adjusted_rating"]
    assert sig_m1["confidence"] > sig_m20["confidence"]
    assert sig_m1["adjusted_rating"] == pytest.approx(4.25, abs=1e-4)


def test_feedback_weight_zero_reproduces_baseline_hybrid_score():
    candidate = {
        "tutor_id": "t_test",
        "name": "Test Tutor",
        "hybrid_score": 0.9450,
        "rating": 4.8,
        "review_count": 25,
    }
    eval_res = evaluate_candidate(candidate, feedback_weight=0.00, smoothing_m=5.0)
    assert eval_res["experimental_score"] == pytest.approx(0.9450, abs=1e-5)


def test_feedback_weight_zero_preserves_baseline_ranking():
    scenarios = load_scenarios()
    for sc in scenarios:
        ranked = run_scenario(sc, feedback_weight=0.00, smoothing_m=5.0)
        # Verify rank 1 has highest hybrid score
        assert ranked[0]["hybrid_score"] >= ranked[1]["hybrid_score"]


def test_experimental_ranking_calculations_are_deterministic():
    scenarios = load_scenarios()
    sc1 = scenarios[0]
    res1 = run_scenario(sc1, feedback_weight=0.15, smoothing_m=5.0)
    res2 = run_scenario(sc1, feedback_weight=0.15, smoothing_m=5.0)
    assert res1 == res2


def test_ranking_flip_detection():
    scenarios = load_scenarios()
    flip_records = run_ranking_flip_analysis(scenarios, weights=WEIGHT_SWEEP, smoothing_m=5.0)

    # In Scenario 1, baseline top is Tutor B (0.96 vs 0.94)
    # At w=0.10, Tutor A (0.94 / 4.8) should flip to rank 1
    s1_w0 = next(r for r in flip_records if r["scenario_id"] == "scenario_1_quality_vs_compatibility" and r["feedback_weight"] == 0.00)
    s1_w10 = next(r for r in flip_records if r["scenario_id"] == "scenario_1_quality_vs_compatibility" and r["feedback_weight"] == 0.10)

    assert s1_w0["rank_flipped"] is False
    assert s1_w0["baseline_top_id"] == "tutor_1b"

    assert s1_w10["rank_flipped"] is True
    assert s1_w10["experimental_top_id"] == "tutor_1a"


def test_production_matching_weights_remain_unmodified():
    # Strict safety invariant
    assert DEFAULT_WEIGHT_LEARNING_NEED == 0.45
    assert DEFAULT_WEIGHT_LOCATION == 0.20
    assert DEFAULT_WEIGHT_FEE == 0.20
    assert DEFAULT_WEIGHT_TIME == 0.15
