import pytest
import math
from unittest.mock import MagicMock
from evaluation.matching.evaluate_matcher import (
    MatchingEvaluator,
    compute_precision_at_k,
    compute_recall_at_k,
    compute_mrr,
    compute_dcg_at_k,
    compute_ndcg_at_k,
    compute_pairwise_ranking_accuracy,
    load_benchmark_data
)


def test_metric_precision_recall_hand_checkable():
    # Ranked IDs: ["t1", "t2", "t3", "t4", "t5"]
    # Qrels: t1=3 (rel), t2=1 (not rel), t3=2 (rel), t4=0 (not rel), t5=3 (rel)
    # Total relevant in qrels: 3 (t1, t3, t5)
    ranked = ["t1", "t2", "t3", "t4", "t5"]
    qrels = {"t1": 3, "t2": 1, "t3": 2, "t4": 0, "t5": 3}

    # Precision@1: top 1 is t1 (rel=3 >= 2) -> 1/1 = 1.0
    assert compute_precision_at_k(ranked, qrels, k=1) == 1.0

    # Precision@3: top 3 has t1 (rel=3), t2 (rel=1), t3 (rel=2) -> 2/3 = 0.6667
    assert abs(compute_precision_at_k(ranked, qrels, k=3) - (2.0 / 3.0)) < 1e-4

    # Precision@5: 3 relevant out of 5 -> 3/5 = 0.60
    assert compute_precision_at_k(ranked, qrels, k=5) == 0.60

    # Recall@5: 3 relevant retrieved out of 3 total relevant -> 3/3 = 1.0
    assert compute_recall_at_k(ranked, qrels, k=5) == 1.0

    # Recall@2: top 2 has 1 relevant out of 3 total relevant -> 1/3 = 0.3333
    assert abs(compute_recall_at_k(ranked, qrels, k=2) - (1.0 / 3.0)) < 1e-4


def test_metric_mrr_calculation():
    # First relevant item is at rank 1
    assert compute_mrr(["t1", "t2"], {"t1": 3, "t2": 0}) == 1.0

    # First relevant item is at rank 2
    assert compute_mrr(["t1", "t2"], {"t1": 1, "t2": 2}) == 0.5

    # First relevant item is at rank 4
    assert compute_mrr(["t1", "t2", "t3", "t4"], {"t1": 0, "t2": 1, "t3": 1, "t4": 3}) == 0.25

    # No relevant items in ranked list -> MRR = 0.0
    assert compute_mrr(["t1", "t2"], {"t1": 0, "t2": 1}) == 0.0
    assert compute_mrr([], {"t1": 3}) == 0.0


def test_metric_ndcg_calculation_and_edge_cases():
    # Perfect ranking: t1 (rel=3), t2 (rel=2), t3 (rel=1)
    ranked = ["t1", "t2", "t3"]
    qrels = {"t1": 3, "t2": 2, "t3": 1}
    assert abs(compute_ndcg_at_k(ranked, qrels, k=3) - 1.0) < 1e-5

    # Inverted ranking: t3 (rel=1), t2 (rel=2), t1 (rel=3)
    ranked_inv = ["t3", "t2", "t1"]
    ndcg_inv = compute_ndcg_at_k(ranked_inv, qrels, k=3)
    assert ndcg_inv < 1.0
    assert ndcg_inv > 0.5

    # Edge case: Query with no relevant documents (all 0s) -> NDCG = 0.0
    qrels_zero = {"t1": 0, "t2": 0}
    assert compute_ndcg_at_k(["t1", "t2"], qrels_zero, k=2) == 0.0

    # Edge case: Empty ranking -> NDCG = 0.0
    assert compute_ndcg_at_k([], qrels, k=3) == 0.0


def test_pairwise_ranking_accuracy():
    # Ranked items with scores: t1=0.9, t2=0.7, t3=0.4
    # Qrels: t1=3, t2=2, t3=0
    # Pairs with distinct relevance:
    # (t1, t2): 3 > 2, score 0.9 > 0.7 -> concordant (1.0)
    # (t1, t3): 3 > 0, score 0.9 > 0.4 -> concordant (1.0)
    # (t2, t3): 2 > 0, score 0.7 > 0.4 -> concordant (1.0)
    # Pairwise accuracy = 3 / 3 = 1.0
    ranked = [
        {"id": "t1", "overall_score": 0.9},
        {"id": "t2", "overall_score": 0.7},
        {"id": "t3", "overall_score": 0.4}
    ]
    qrels = {"t1": 3, "t2": 2, "t3": 0}
    acc = compute_pairwise_ranking_accuracy(ranked, qrels)
    assert acc == 1.0

    # Tied score gives 0.5 penalty
    ranked_tied = [
        {"id": "t1", "overall_score": 0.8},
        {"id": "t2", "overall_score": 0.8},
        {"id": "t3", "overall_score": 0.4}
    ]
    # (t1, t2): tie -> 0.5; (t1, t3): concordant -> 1.0; (t2, t3): concordant -> 1.0
    # Total = (0.5 + 1.0 + 1.0) / 3 = 2.5 / 3 = 0.8333
    acc_tied = compute_pairwise_ranking_accuracy(ranked_tied, qrels)
    assert abs(acc_tied - (2.5 / 3.0)) < 1e-4


def test_benchmark_data_loading_and_relevance_grades():
    queries, tutors, qrels = load_benchmark_data()
    assert len(queries) >= 5
    assert len(tutors) >= 10
    assert len(qrels) == len(queries)

    # Verify every qrel value is valid grade in {0, 1, 2, 3}
    for qid, judgments in qrels.items():
        assert isinstance(judgments, dict)
        for tid, grade in judgments.items():
            assert grade in {0, 1, 2, 3}, f"Invalid grade {grade} for {qid}->{tid}"


def test_legacy_baseline_does_not_call_embeddings():
    mock_embedder = MagicMock()
    evaluator = MatchingEvaluator(embedding_service=mock_embedder)

    query = {
        "subjects_needed": "Physics",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "budget_min": 400.0,
        "budget_max": 800.0,
        "preferred_slots": []
    }
    tutor = {
        "tutor_id": "t1",
        "subjects_taught": ["Physics"],
        "hourly_rate": 500.0,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "availability": [],
        "rating": 4.8,
        "is_verified": True
    }

    results = evaluator.run_legacy_baseline(query, [tutor])
    assert len(results) == 1
    # Verify embedding encode method was NEVER called during baseline execution
    mock_embedder.encode.assert_not_called()
    mock_embedder.compute_similarity.assert_not_called()


def test_legacy_baseline_assigns_unit_subject_score():
    mock_embedder = MagicMock()
    evaluator = MatchingEvaluator(embedding_service=mock_embedder)

    query = {
        "subjects_needed": "Mathematics",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "budget_min": 300.0,
        "budget_max": 1000.0,
        "preferred_slots": []
    }
    # Two tutors in Mathematics at same location, budget, availability
    tutor_a = {
        "tutor_id": "ta",
        "subjects_taught": ["Mathematics"],
        "hourly_rate": 500.0,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "availability": [],
        "rating": 4.5,
        "is_verified": True
    }
    tutor_b = {
        "tutor_id": "tb",
        "subjects_taught": ["Mathematics"],
        "hourly_rate": 500.0,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "availability": [],
        "rating": 4.5,
        "is_verified": True
    }

    results = evaluator.run_legacy_baseline(query, [tutor_a, tutor_b])
    assert len(results) == 2
    # Both receive identical baseline score = 0.40(1.0) + 0.20(1.0) + 0.20(1.0) + 0.20(1.0) = 1.0
    assert results[0]["overall_score"] == 1.0
    assert results[1]["overall_score"] == 1.0


def test_semantic_vs_topic_vs_hybrid_formulation():
    mock_embedder = MagicMock()
    # Mock embedding similarity return: tutor_1=0.90, tutor_2=0.40
    mock_embedder.compute_similarity.return_value = [0.90, 0.40]
    mock_embedder.encode.return_value = MagicMock()

    evaluator = MatchingEvaluator(embedding_service=mock_embedder)

    query = {
        "subjects_needed": "Physics",
        "topics": ["Rotational Motion"],
        "latitude": 13.0827,
        "longitude": 80.2707,
        "budget_min": 300.0,
        "budget_max": 1000.0,
        "preferred_slots": []
    }
    # Tutor 1: topic matches exact "Rotational Motion"
    tutor_1 = {
        "tutor_id": "t1",
        "subjects_taught": ["Physics"],
        "topics_expertise": ["Rotational Motion"],
        "hourly_rate": 500.0,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "availability": [],
        "rating": 4.5,
        "is_verified": True
    }
    # Tutor 2: topic unrelated "Optics"
    tutor_2 = {
        "tutor_id": "t2",
        "subjects_taught": ["Physics"],
        "topics_expertise": ["Optics"],
        "hourly_rate": 500.0,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "availability": [],
        "rating": 4.5,
        "is_verified": True
    }

    # 1. Run Semantic Only
    sem_results = evaluator.run_dense_semantic_only(query, [tutor_1, tutor_2])
    # t1 sem_score=0.90 -> 0.45*0.90 + 0.20*1 + 0.20*1 + 0.15*1 = 0.405 + 0.55 = 0.955
    # t2 sem_score=0.40 -> 0.45*0.40 + 0.55 = 0.18 + 0.55 = 0.73
    assert abs(sem_results[0]["overall_score"] - 0.955) < 1e-4

    # 2. Run Topic Only
    # t1 topic_score=1.0 -> 0.45*1.0 + 0.55 = 1.0
    # t2 topic_score=0.0 -> 0.45*0.0 + 0.55 = 0.55
    topic_results = evaluator.run_topic_overlap_only(query, [tutor_1, tutor_2])
    assert abs(topic_results[0]["overall_score"] - 1.0) < 1e-4
    assert abs(topic_results[1]["overall_score"] - 0.55) < 1e-4

    # 3. Run Hybrid:
    # t1 ln_score = 0.60*0.90 + 0.40*1.0 = 0.54 + 0.40 = 0.94
    # t1 overall = 0.45*0.94 + 0.55 = 0.423 + 0.55 = 0.973
    hybrid_results = evaluator.run_full_hybrid(query, [tutor_1, tutor_2])
    assert abs(hybrid_results[0]["overall_score"] - 0.973) < 1e-4


def test_evaluation_determinism_and_no_biometrics():
    mock_embedder = MagicMock()
    mock_embedder.compute_similarity.return_value = [0.85]
    evaluator = MatchingEvaluator(embedding_service=mock_embedder)

    query = {
        "query_id": "q_test",
        "subjects_needed": "Physics",
        "topics": ["Kinematics"],
        "latitude": 13.0827,
        "longitude": 80.2707,
        "budget_min": 400.0,
        "budget_max": 800.0,
        "preferred_slots": []
    }
    tutor = {
        "tutor_id": "t_test",
        "subjects_taught": ["Physics"],
        "topics_expertise": ["Kinematics"],
        "hourly_rate": 500.0,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "availability": [],
        "rating": 4.8,
        "is_verified": True
    }
    qrels = {"q_test": {"t_test": 3}}

    # Run twice
    res1 = evaluator.evaluate_configuration("D_Full_Hybrid", evaluator.run_full_hybrid, [query], [tutor], qrels)
    res2 = evaluator.evaluate_configuration("D_Full_Hybrid", evaluator.run_full_hybrid, [query], [tutor], qrels)

    # Must be 100% strictly identical
    assert res1 == res2
    assert "face" not in str(res1).lower()
    assert "biometric" not in str(res1).lower()
