"""
Offline Evaluation Harness for TutorLinkAI Matching Engine.

Performs deterministic experimental comparison across five distinct configurations:
  Configuration A: Legacy Baseline (Subject Gate + Distance/Fee/Time Constraints, Subject Score = 1.0)
  Configuration B: Dense Semantic Only (Subject Gate + S-BERT Cosine Similarity + Constraints)
  Configuration C: Topic Overlap Only (Subject Gate + Deterministic Token/Substring Overlap + Constraints)
  Configuration D: Full Hybrid Matcher (Production Step 3C: Subject Gate + 0.60 Semantic / 0.40 Topic Fusion + Constraints)
  Configuration E: Full Hybrid + Feedback (Step 6A Research Experiment: Bayesian Feedback Signal + Hybrid Base)

Metrics computed:
  - Precision@1, Precision@3, Precision@5
  - Recall@5
  - MRR (Mean Reciprocal Rank)
  - NDCG@3, NDCG@5
  - Pairwise Ranking Accuracy

All benchmark data is loaded entirely offline from JSON files.
"""
import os
import sys
import json
import math
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Ensure project root and ai-service are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AI_SERVICE_DIR = BASE_DIR / "ai-service"
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.matching.embeddings import EmbeddingService, get_embedding_service
from app.matching.taxonomy import evaluate_subject_gate
from app.matching.scoring import (
    calculate_location_score,
    calculate_fee_score,
    calculate_time_score,
    calculate_topic_overlap,
    calculate_learning_need_score,
    calculate_composite_score,
)
from app.matching.matcher import build_student_semantic_text, build_tutor_semantic_text
from backend.app.services.feedback_score import calculate_feedback_signal, DEFAULT_SMOOTHING_M, DEFAULT_GLOBAL_PRIOR


def load_benchmark_data(data_dir: Optional[Path] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Dict[str, int]]]:
    """
    Loads queries.json, tutors.json, and qrels.json from the evaluation directory.
    """
    if data_dir is None:
        data_dir = Path(__file__).resolve().parent

    queries_file = data_dir / "queries.json"
    tutors_file = data_dir / "tutors.json"
    qrels_file = data_dir / "qrels.json"

    if not queries_file.exists():
        raise FileNotFoundError(f"Missing benchmark queries file: {queries_file}")
    if not tutors_file.exists():
        raise FileNotFoundError(f"Missing benchmark tutors file: {tutors_file}")
    if not qrels_file.exists():
        raise FileNotFoundError(f"Missing benchmark qrels file: {qrels_file}")

    with open(queries_file, "r", encoding="utf-8") as f:
        queries = json.load(f)
    with open(tutors_file, "r", encoding="utf-8") as f:
        tutors = json.load(f)
    with open(qrels_file, "r", encoding="utf-8") as f:
        qrels = json.load(f)

    return queries, tutors, qrels


# =============================================================================
# METRIC CALCULATION FUNCTIONS
# =============================================================================

def compute_precision_at_k(
    ranked_tutor_ids: List[str],
    query_qrels: Dict[str, int],
    k: int,
    relevance_threshold: int = 2,
) -> float:
    """
    Computes Precision@K:
    Number of retrieved items in top-K with relevance >= relevance_threshold divided by K.
    """
    if k <= 0:
        return 0.0
    top_k = ranked_tutor_ids[:k]
    if not top_k:
        return 0.0
    relevant_count = sum(
        1 for tid in top_k if query_qrels.get(tid, 0) >= relevance_threshold
    )
    return relevant_count / float(k)


def compute_recall_at_k(
    ranked_tutor_ids: List[str],
    query_qrels: Dict[str, int],
    k: int,
    relevance_threshold: int = 2,
) -> float:
    """
    Computes Recall@K:
    Number of retrieved relevant items in top-K divided by total relevant items in ground truth.
    """
    total_relevant = sum(
        1 for rel in query_qrels.values() if rel >= relevance_threshold
    )
    if total_relevant == 0:
        return 0.0
    top_k = ranked_tutor_ids[:k]
    retrieved_relevant = sum(
        1 for tid in top_k if query_qrels.get(tid, 0) >= relevance_threshold
    )
    return retrieved_relevant / float(total_relevant)


def compute_mrr(
    ranked_tutor_ids: List[str],
    query_qrels: Dict[str, int],
    relevance_threshold: int = 2,
) -> float:
    """
    Computes Mean Reciprocal Rank (MRR):
    1 / rank of first relevant item (relevance >= relevance_threshold).
    Returns 0.0 if no relevant items are in the ranked list.
    """
    for rank_idx, tid in enumerate(ranked_tutor_ids, start=1):
        if query_qrels.get(tid, 0) >= relevance_threshold:
            return 1.0 / float(rank_idx)
    return 0.0


def compute_dcg_at_k(
    ranked_tutor_ids: List[str],
    query_qrels: Dict[str, int],
    k: int,
) -> float:
    """
    Computes Discounted Cumulative Gain (DCG@K) using standard graded exponential gain:
    DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log2(i + 1)
    """
    top_k = ranked_tutor_ids[:k]
    dcg = 0.0
    for i, tid in enumerate(top_k, start=1):
        rel = query_qrels.get(tid, 0)
        gain = (2.0 ** rel) - 1.0
        discount = math.log2(i + 1)
        dcg += gain / discount
    return dcg


def compute_ndcg_at_k(
    ranked_tutor_ids: List[str],
    query_qrels: Dict[str, int],
    k: int,
) -> float:
    """
    Computes Normalized Discounted Cumulative Gain (NDCG@K).
    Returns 0.0 if Ideal DCG (IDCG@K) is 0.
    """
    actual_dcg = compute_dcg_at_k(ranked_tutor_ids, query_qrels, k)

    # Sort all ground truth grades in descending order for ideal DCG
    all_grades = sorted(query_qrels.values(), reverse=True)
    top_k_ideal = all_grades[:k]
    idcg = 0.0
    for i, rel in enumerate(top_k_ideal, start=1):
        gain = (2.0 ** rel) - 1.0
        discount = math.log2(i + 1)
        idcg += gain / discount

    if idcg <= 0.0:
        return 0.0

    return actual_dcg / idcg


def compute_pairwise_ranking_accuracy(
    ranked_results: List[Dict[str, Any]],
    query_qrels: Dict[str, int],
) -> Optional[float]:
    """
    Computes Pairwise Ranking Accuracy:
    For all pairs of candidate tutors (A, B) where ground truth Grade(A) > Grade(B):
      - Concordant (Score(A) > Score(B)) -> 1.0
      - Tied (Score(A) == Score(B)) -> 0.5
      - Discordant (Score(A) < Score(B)) -> 0.0
    Returns None if no candidate pairs with distinct relevance grades exist.
    """
    score_map = {item["id"]: item["overall_score"] for item in ranked_results}
    all_tids = list(query_qrels.keys())

    concordant = 0.0
    total_pairs = 0

    for i in range(len(all_tids)):
        for j in range(i + 1, len(all_tids)):
            tid_a = all_tids[i]
            tid_b = all_tids[j]
            grade_a = query_qrels.get(tid_a, 0)
            grade_b = query_qrels.get(tid_b, 0)

            if grade_a == grade_b:
                continue

            # Ensure A is the higher-relevance item
            if grade_a < grade_b:
                tid_a, tid_b = tid_b, tid_a
                grade_a, grade_b = grade_b, grade_a

            total_pairs += 1
            score_a = score_map.get(tid_a, 0.0)
            score_b = score_map.get(tid_b, 0.0)

            if score_a > score_b:
                concordant += 1.0
            elif score_a == score_b:
                concordant += 0.5

    if total_pairs == 0:
        return None

    return concordant / float(total_pairs)


# =============================================================================
# EXPERIMENTAL CONFIGURATIONS RUNNER
# =============================================================================

class MatchingEvaluator:
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or get_embedding_service()

    def run_legacy_baseline(
        self, query: Dict[str, Any], candidate_tutors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Configuration A: Legacy Baseline
        - Stage 1: Strict Subject Gate
        - Passing candidates receive subject_score = 1.0
        - Score: 0.40 * 1.0 + 0.20 * location + 0.20 * fee + 0.20 * time
        - NO semantic embeddings, NO topic overlap.
        """
        subject_needed = str(query.get("subjects_needed", "")).strip()
        student_lat = float(query.get("latitude", 13.0827))
        student_lon = float(query.get("longitude", 80.2707))
        budget_min = float(query.get("budget_min", 300.0))
        budget_max = float(query.get("budget_max", 1000.0))
        preferred_slots = query.get("preferred_slots", [])

        ranked = []
        for tutor in candidate_tutors:
            if tutor.get("is_verified") is False:
                continue

            tutor_subjects = tutor.get("subjects") or tutor.get("subjects_taught") or []
            is_eligible, _ = evaluate_subject_gate(
                requested_subject=subject_needed,
                tutor_subjects=tutor_subjects,
                embedding_service=self.embedding_service,
            )
            if not is_eligible:
                continue

            # Fixed historical subject score = 1.0
            subject_score = 1.0

            t_lat = float(tutor.get("latitude", 0.0))
            t_lon = float(tutor.get("longitude", 0.0))
            loc_score, _ = calculate_location_score(student_lat, student_lon, t_lat, t_lon)

            rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(rate, budget_min, budget_max)

            availability = tutor.get("availability", [])
            time_sc = calculate_time_score(preferred_slots, availability)

            # Historical baseline formula
            overall = (
                (0.40 * subject_score)
                + (0.20 * loc_score)
                + (0.20 * fee_sc)
                + (0.20 * time_sc)
            )

            ranked.append({
                "id": tutor.get("tutor_id") or tutor.get("id"),
                "overall_score": float(overall),
                "rating": float(tutor.get("rating") or 4.5),
            })

        # Deterministic sort
        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def run_dense_semantic_only(
        self, query: Dict[str, Any], candidate_tutors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Configuration B: Dense Semantic Only
        - Stage 1: Strict Subject Gate
        - Score: 0.45 * semantic_score + 0.20 * location + 0.20 * fee + 0.15 * time
        - NO topic overlap.
        """
        subject_needed = str(query.get("subjects_needed", "")).strip()
        student_lat = float(query.get("latitude", 13.0827))
        student_lon = float(query.get("longitude", 80.2707))
        budget_min = float(query.get("budget_min", 300.0))
        budget_max = float(query.get("budget_max", 1000.0))
        preferred_slots = query.get("preferred_slots", [])

        # Stage 1 Gate
        qualified = []
        for tutor in candidate_tutors:
            if tutor.get("is_verified") is False:
                continue
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            is_eligible, _ = evaluate_subject_gate(subject_needed, t_subs, self.embedding_service)
            if is_eligible:
                qualified.append(tutor)

        if not qualified:
            return []

        # Encode query text
        s_text = build_student_semantic_text(query)
        s_emb = self.embedding_service.encode([s_text])

        # Encode tutor capability texts
        t_texts = [
            build_tutor_semantic_text(t, t.get("subjects") or t.get("subjects_taught") or [])
            for t in qualified
        ]
        t_embs = self.embedding_service.encode(t_texts)
        sims = self.embedding_service.compute_similarity(s_emb, t_embs)

        ranked = []
        for i, tutor in enumerate(qualified):
            sem_score = float(sims[i])
            t_lat = float(tutor.get("latitude", 0.0))
            t_lon = float(tutor.get("longitude", 0.0))
            loc_score, _ = calculate_location_score(student_lat, student_lon, t_lat, t_lon)
            rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(rate, budget_min, budget_max)
            time_sc = calculate_time_score(preferred_slots, tutor.get("availability", []))

            overall = (
                (0.45 * sem_score)
                + (0.20 * loc_score)
                + (0.20 * fee_sc)
                + (0.15 * time_sc)
            )

            ranked.append({
                "id": tutor.get("tutor_id") or tutor.get("id"),
                "overall_score": float(overall),
                "rating": float(tutor.get("rating") or 4.5),
            })

        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def run_topic_overlap_only(
        self, query: Dict[str, Any], candidate_tutors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Configuration C: Topic Overlap Only
        - Stage 1: Strict Subject Gate
        - Score: 0.45 * topic_score + 0.20 * location + 0.20 * fee + 0.15 * time
        - NO dense semantic embeddings.
        """
        subject_needed = str(query.get("subjects_needed", "")).strip()
        student_lat = float(query.get("latitude", 13.0827))
        student_lon = float(query.get("longitude", 80.2707))
        budget_min = float(query.get("budget_min", 300.0))
        budget_max = float(query.get("budget_max", 1000.0))
        preferred_slots = query.get("preferred_slots", [])
        student_topics = query.get("topics") or []

        ranked = []
        for tutor in candidate_tutors:
            if tutor.get("is_verified") is False:
                continue
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            is_eligible, _ = evaluate_subject_gate(subject_needed, t_subs, self.embedding_service)
            if not is_eligible:
                continue

            t_topics = tutor.get("topics_expertise") or []
            combined_t_topics = list(set(t_topics + t_subs))
            topic_score, _ = calculate_topic_overlap(student_topics, combined_t_topics)

            t_lat = float(tutor.get("latitude", 0.0))
            t_lon = float(tutor.get("longitude", 0.0))
            loc_score, _ = calculate_location_score(student_lat, student_lon, t_lat, t_lon)
            rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(rate, budget_min, budget_max)
            time_sc = calculate_time_score(preferred_slots, tutor.get("availability", []))

            overall = (
                (0.45 * topic_score)
                + (0.20 * loc_score)
                + (0.20 * fee_sc)
                + (0.15 * time_sc)
            )

            ranked.append({
                "id": tutor.get("tutor_id") or tutor.get("id"),
                "overall_score": float(overall),
                "rating": float(tutor.get("rating") or 4.5),
            })

        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def run_full_hybrid(
        self, query: Dict[str, Any], candidate_tutors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Configuration D: Full Hybrid Matcher (Production Step 3C Formulation)
        - Stage 1: Strict Subject Gate
        - learning_need_score = 0.60 * semantic_score + 0.40 * topic_score (or 1.0 * semantic_score if no topics)
        - Score: 0.45 * learning_need_score + 0.20 * location + 0.20 * fee + 0.15 * time
        """
        subject_needed = str(query.get("subjects_needed", "")).strip()
        student_lat = float(query.get("latitude", 13.0827))
        student_lon = float(query.get("longitude", 80.2707))
        budget_min = float(query.get("budget_min", 300.0))
        budget_max = float(query.get("budget_max", 1000.0))
        preferred_slots = query.get("preferred_slots", [])
        student_topics = query.get("topics") or []

        qualified = []
        for tutor in candidate_tutors:
            if tutor.get("is_verified") is False:
                continue
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            is_eligible, _ = evaluate_subject_gate(subject_needed, t_subs, self.embedding_service)
            if is_eligible:
                qualified.append(tutor)

        if not qualified:
            return []

        s_text = build_student_semantic_text(query)
        s_emb = self.embedding_service.encode([s_text])

        t_texts = [
            build_tutor_semantic_text(t, t.get("subjects") or t.get("subjects_taught") or [])
            for t in qualified
        ]
        t_embs = self.embedding_service.encode(t_texts)
        sims = self.embedding_service.compute_similarity(s_emb, t_embs)

        ranked = []
        for i, tutor in enumerate(qualified):
            sem_score = float(sims[i])
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            t_topics = tutor.get("topics_expertise") or []
            combined_t_topics = list(set(t_topics + t_subs))
            topic_score, _ = calculate_topic_overlap(student_topics, combined_t_topics)

            has_topics = bool(student_topics)
            ln_score = calculate_learning_need_score(sem_score, topic_score, has_topics)

            t_lat = float(tutor.get("latitude", 0.0))
            t_lon = float(tutor.get("longitude", 0.0))
            loc_score, _ = calculate_location_score(student_lat, student_lon, t_lat, t_lon)
            rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(rate, budget_min, budget_max)
            time_sc = calculate_time_score(preferred_slots, tutor.get("availability", []))

            overall = (
                (0.45 * ln_score)
                + (0.20 * loc_score)
                + (0.20 * fee_sc)
                + (0.15 * time_sc)
            )

            ranked.append({
                "id": tutor.get("tutor_id") or tutor.get("id"),
                "overall_score": float(overall),
                "rating": float(tutor.get("rating") or 4.5),
            })

        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def run_full_hybrid_with_feedback(
        self,
        query: Dict[str, Any],
        candidate_tutors: List[Dict[str, Any]],
        feedback_weight: float = 0.10,
        smoothing_m: float = DEFAULT_SMOOTHING_M,
        global_prior: float = DEFAULT_GLOBAL_PRIOR,
    ) -> List[Dict[str, Any]]:
        """
        Configuration E: Full Hybrid + Feedback Signal (Offline Research Experiment)
        - Base Hybrid Score (Configuration D)
        - Bayesian feedback signal calculated via calculate_feedback_signal()
        - Experimental Composite: (1 - feedback_weight) * base_score + feedback_weight * feedback_score
        """
        subject_needed = str(query.get("subjects_needed", "")).strip()
        student_lat = float(query.get("latitude", 13.0827))
        student_lon = float(query.get("longitude", 80.2707))
        budget_min = float(query.get("budget_min", 300.0))
        budget_max = float(query.get("budget_max", 1000.0))
        preferred_slots = query.get("preferred_slots", [])
        student_topics = query.get("topics") or []

        qualified = []
        for tutor in candidate_tutors:
            if tutor.get("is_verified") is False:
                continue
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            is_eligible, _ = evaluate_subject_gate(subject_needed, t_subs, self.embedding_service)
            if is_eligible:
                qualified.append(tutor)

        if not qualified:
            return []

        s_text = build_student_semantic_text(query)
        s_emb = self.embedding_service.encode([s_text])

        t_texts = [
            build_tutor_semantic_text(t, t.get("subjects") or t.get("subjects_taught") or [])
            for t in qualified
        ]
        t_embs = self.embedding_service.encode(t_texts)
        sims = self.embedding_service.compute_similarity(s_emb, t_embs)

        ranked = []
        for i, tutor in enumerate(qualified):
            sem_score = float(sims[i])
            t_subs = tutor.get("subjects") or tutor.get("subjects_taught") or []
            t_topics = tutor.get("topics_expertise") or []
            combined_t_topics = list(set(t_topics + t_subs))
            topic_score, _ = calculate_topic_overlap(student_topics, combined_t_topics)

            has_topics = bool(student_topics)
            ln_score = calculate_learning_need_score(sem_score, topic_score, has_topics)

            t_lat = float(tutor.get("latitude", 0.0))
            t_lon = float(tutor.get("longitude", 0.0))
            loc_score, _ = calculate_location_score(student_lat, student_lon, t_lat, t_lon)
            rate = float(tutor.get("hourly_rate", 0.0))
            fee_sc = calculate_fee_score(rate, budget_min, budget_max)
            time_sc = calculate_time_score(preferred_slots, tutor.get("availability", []))

            base_overall = (
                (0.45 * ln_score)
                + (0.20 * loc_score)
                + (0.20 * fee_sc)
                + (0.15 * time_sc)
            )

            # Compute Bayesian feedback signal
            t_rating = tutor.get("rating")
            t_rev_count = tutor.get("review_count", 0)
            fb_sig = calculate_feedback_signal(
                average_rating=t_rating,
                review_count=t_rev_count,
                smoothing_m=smoothing_m,
                global_prior=global_prior,
            )
            feedback_score = fb_sig["feedback_score"]

            # Experimental fusion
            w_fb = max(0.0, min(1.0, float(feedback_weight)))
            experimental_overall = ((1.0 - w_fb) * base_overall) + (w_fb * feedback_score)

            ranked.append({
                "id": tutor.get("tutor_id") or tutor.get("id"),
                "overall_score": float(experimental_overall),
                "base_score": float(base_overall),
                "feedback_score": float(feedback_score),
                "confidence": float(fb_sig["confidence"]),
                "rating": float(t_rating or global_prior),
                "review_count": int(t_rev_count),
            })

        ranked.sort(key=lambda x: (round(x["overall_score"], 6), round(x["rating"], 2), x["id"]), reverse=True)
        return ranked

    def evaluate_configuration(
        self,
        config_name: str,
        run_fn,
        queries: List[Dict[str, Any]],
        tutors: List[Dict[str, Any]],
        qrels: Dict[str, Dict[str, int]],
    ) -> Dict[str, Any]:
        """
        Evaluates a specific experimental configuration over all benchmark queries.
        """
        p1_list = []
        p3_list = []
        p5_list = []
        r5_list = []
        mrr_list = []
        ndcg3_list = []
        ndcg5_list = []
        pairwise_acc_list = []

        valid_query_count = 0
        excluded_queries = []

        for q in queries:
            qid = q.get("query_id")
            if not qid or qid not in qrels:
                excluded_queries.append({"query_id": qid, "reason": "No relevance judgments in qrels.json"})
                continue

            query_qrels = qrels[qid]
            ranked_results = run_fn(q, tutors)
            ranked_ids = [item["id"] for item in ranked_results]

            p1 = compute_precision_at_k(ranked_ids, query_qrels, k=1)
            p3 = compute_precision_at_k(ranked_ids, query_qrels, k=3)
            p5 = compute_precision_at_k(ranked_ids, query_qrels, k=5)
            r5 = compute_recall_at_k(ranked_ids, query_qrels, k=5)
            mrr = compute_mrr(ranked_ids, query_qrels)
            ndcg3 = compute_ndcg_at_k(ranked_ids, query_qrels, k=3)
            ndcg5 = compute_ndcg_at_k(ranked_ids, query_qrels, k=5)
            pw_acc = compute_pairwise_ranking_accuracy(ranked_results, query_qrels)

            p1_list.append(p1)
            p3_list.append(p3)
            p5_list.append(p5)
            r5_list.append(r5)
            mrr_list.append(mrr)
            ndcg3_list.append(ndcg3)
            ndcg5_list.append(ndcg5)
            if pw_acc is not None:
                pairwise_acc_list.append(pw_acc)

            valid_query_count += 1

        def _mean(vals: List[float]) -> float:
            return float(round(sum(vals) / len(vals), 4)) if vals else 0.0

        metrics = {
            "configuration": config_name,
            "total_queries": len(queries),
            "valid_queries": valid_query_count,
            "total_candidate_tutors": len(tutors),
            "precision_at_1": _mean(p1_list),
            "precision_at_3": _mean(p3_list),
            "precision_at_5": _mean(p5_list),
            "recall_at_5": _mean(r5_list),
            "mrr": _mean(mrr_list),
            "ndcg_at_3": _mean(ndcg3_list),
            "ndcg_at_5": _mean(ndcg5_list),
            "pairwise_ranking_accuracy": _mean(pairwise_acc_list),
            "excluded_queries": excluded_queries,
        }
        return metrics

    def run_feedback_sensitivity_analysis(
        self,
        queries: List[Dict[str, Any]],
        tutors: List[Dict[str, Any]],
        qrels: Dict[str, Dict[str, int]],
        weights: Optional[List[float]] = None,
        smoothing_m: float = DEFAULT_SMOOTHING_M,
        output_dir: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        Runs sensitivity sweep across experimental feedback weights (e.g. 0.00 to 0.20)
        and outputs feedback_weight_sensitivity.csv.
        """
        if weights is None:
            weights = [0.00, 0.05, 0.10, 0.15, 0.20]

        if output_dir is None:
            output_dir = Path(__file__).resolve().parent / "results"
        output_dir.mkdir(parents=True, exist_ok=True)

        sensitivity_rows = []
        for w in weights:
            fn = lambda q, t, weight=w: self.run_full_hybrid_with_feedback(q, t, feedback_weight=weight, smoothing_m=smoothing_m)
            cfg_name = f"Feedback_Weight_{w:.2f}"
            res = self.evaluate_configuration(cfg_name, fn, queries, tutors, qrels)
            res["feedback_weight"] = w
            res["smoothing_m"] = smoothing_m
            sensitivity_rows.append(res)

        # Export CSV
        csv_path = output_dir / "feedback_weight_sensitivity.csv"
        csv_headers = [
            "feedback_weight",
            "smoothing_m",
            "precision_at_1",
            "precision_at_3",
            "precision_at_5",
            "recall_at_5",
            "mrr",
            "ndcg_at_3",
            "ndcg_at_5",
            "pairwise_ranking_accuracy",
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            for r in sensitivity_rows:
                writer.writerow({
                    "feedback_weight": f"{r['feedback_weight']:.2f}",
                    "smoothing_m": f"{r['smoothing_m']:.1f}",
                    "precision_at_1": r["precision_at_1"],
                    "precision_at_3": r["precision_at_3"],
                    "precision_at_5": r["precision_at_5"],
                    "recall_at_5": r["recall_at_5"],
                    "mrr": r["mrr"],
                    "ndcg_at_3": r["ndcg_at_3"],
                    "ndcg_at_5": r["ndcg_at_5"],
                    "pairwise_ranking_accuracy": r["pairwise_ranking_accuracy"],
                })

        return sensitivity_rows

    def run_all_ablations(
        self,
        data_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        feedback_weight: float = 0.10,
        smoothing_m: float = DEFAULT_SMOOTHING_M,
    ) -> Dict[str, Any]:
        """
        Executes all 5 experimental configurations (A, B, C, D, E) and sensitivity analysis,
        exporting JSON and CSV reports.
        """
        if data_dir is None:
            data_dir = Path(__file__).resolve().parent
        if output_dir is None:
            output_dir = data_dir / "results"

        output_dir.mkdir(parents=True, exist_ok=True)

        queries, tutors, qrels = load_benchmark_data(data_dir)

        feedback_fn = lambda q, t: self.run_full_hybrid_with_feedback(
            q, t, feedback_weight=feedback_weight, smoothing_m=smoothing_m
        )

        configs = [
            ("A_Legacy_Baseline", self.run_legacy_baseline),
            ("B_Dense_Semantic", self.run_dense_semantic_only),
            ("C_Topic_Overlap", self.run_topic_overlap_only),
            ("D_Full_Hybrid", self.run_full_hybrid),
            ("E_Full_Hybrid_Feedback", feedback_fn),
        ]

        results = {}
        for name, fn in configs:
            results[name] = self.evaluate_configuration(name, fn, queries, tutors, qrels)

        # Run sensitivity analysis
        self.run_feedback_sensitivity_analysis(
            queries, tutors, qrels, weights=[0.00, 0.05, 0.10, 0.15, 0.20], smoothing_m=smoothing_m, output_dir=output_dir
        )

        # Export JSON
        json_path = output_dir / "ablation_results.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        # Export CSV
        csv_path = output_dir / "ablation_results.csv"
        csv_headers = [
            "configuration",
            "valid_queries",
            "total_tutors",
            "precision_at_1",
            "precision_at_3",
            "precision_at_5",
            "recall_at_5",
            "mrr",
            "ndcg_at_3",
            "ndcg_at_5",
            "pairwise_ranking_accuracy",
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers)
            writer.writeheader()
            for row in results.values():
                writer.writerow({
                    "configuration": row["configuration"],
                    "valid_queries": row["valid_queries"],
                    "total_tutors": row["total_candidate_tutors"],
                    "precision_at_1": row["precision_at_1"],
                    "precision_at_3": row["precision_at_3"],
                    "precision_at_5": row["precision_at_5"],
                    "recall_at_5": row["recall_at_5"],
                    "mrr": row["mrr"],
                    "ndcg_at_3": row["ndcg_at_3"],
                    "ndcg_at_5": row["ndcg_at_5"],
                    "pairwise_ranking_accuracy": row["pairwise_ranking_accuracy"],
                })

        return results


def main():
    parser = argparse.ArgumentParser(description="TutorLinkAI Matching Offline Evaluation & Feedback Signal Experiment")
    parser.add_argument("--feedback-weight", type=float, default=0.10, help="Experimental feedback signal weight (default: 0.10)")
    parser.add_argument("--smoothing-m", type=float, default=DEFAULT_SMOOTHING_M, help="Bayesian shrinkage smoothing parameter m (default: 5.0)")
    args = parser.parse_args()

    print("=================================================================")
    print("TutorLinkAI — Offline Matching Evaluation Harness (Step 6A)")
    print(f"Experimental Parameters: feedback_weight={args.feedback_weight:.2f}, smoothing_m={args.smoothing_m:.1f}")
    print("=================================================================")

    evaluator = MatchingEvaluator()
    results = evaluator.run_all_ablations(feedback_weight=args.feedback_weight, smoothing_m=args.smoothing_m)

    print("\nBenchmark Evaluation Results Summary:")
    print("-" * 115)
    print(f"{'Configuration':<26} | {'P@1':<6} | {'P@3':<6} | {'P@5':<6} | {'R@5':<6} | {'MRR':<6} | {'NDCG@3':<7} | {'NDCG@5':<7} | {'PairwiseAcc':<11}")
    print("-" * 115)
    for res in results.values():
        print(
            f"{res['configuration']:<26} | "
            f"{res['precision_at_1']:<6.4f} | "
            f"{res['precision_at_3']:<6.4f} | "
            f"{res['precision_at_5']:<6.4f} | "
            f"{res['recall_at_5']:<6.4f} | "
            f"{res['mrr']:<6.4f} | "
            f"{res['ndcg_at_3']:<7.4f} | "
            f"{res['ndcg_at_5']:<7.4f} | "
            f"{res['pairwise_ranking_accuracy']:<11.4f}"
        )
    print("-" * 115)
    print("\nEvaluation completed. Results saved to evaluation/matching/results/\n")


if __name__ == "__main__":
    main()
