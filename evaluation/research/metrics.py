"""
Standard Information Retrieval & Recommendation Ranking Metrics.
Provides mathematically rigorous, deterministic implementations for:
- Precision@K (K in [1, 3, 5])
- Recall@K (K=5)
- Mean Reciprocal Rank (MRR)
- Discounted Cumulative Gain (DCG@K)
- Normalized Discounted Cumulative Gain (NDCG@K, K in [3, 5])
- Pairwise Ranking Accuracy (Concordant Pair Ratio)
"""
import math
from typing import Dict, List, Any, Optional

from evaluation.research.config import (
    PRECISION_K_VALUES,
    RECALL_K_VALUES,
    NDCG_K_VALUES,
    DEFAULT_RELEVANCE_THRESHOLD,
)


def compute_precision_at_k(
    ranked_tutor_ids: List[str],
    query_qrels: Dict[str, int],
    k: int,
    relevance_threshold: int = DEFAULT_RELEVANCE_THRESHOLD,
) -> float:
    """
    Computes Precision@K:
    $$\\text{Precision}@K = \\frac{1}{K} \\sum_{i=1}^K \\mathbb{I}(\\text{rel}_i \\ge \\tau)$$
    Where:
    - $\\text{rel}_i$ is the ground-truth relevance grade of the item at rank $i$.
    - $\\tau$ is the binary relevance threshold (default $\\tau = 2$).
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
    relevance_threshold: int = DEFAULT_RELEVANCE_THRESHOLD,
) -> float:
    """
    Computes Recall@K:
    $$\\text{Recall}@K = \\frac{\\sum_{i=1}^K \\mathbb{I}(\\text{rel}_i \\ge \\tau)}{\\sum_{j \\in \\mathcal{D}} \\mathbb{I}(\\text{rel}_j \\ge \\tau)}$$
    Proportion of all relevant items in the candidate pool retrieved in the top-K ranking.
    Returns 0.0 if no relevant items exist in ground truth.
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
    relevance_threshold: int = DEFAULT_RELEVANCE_THRESHOLD,
) -> float:
    """
    Computes Reciprocal Rank (RR):
    $$\\text{RR} = \\frac{1}{\\min \\{ i \\mid \\text{rel}_i \\ge \\tau \\}}$$
    Returns 0.0 if no retrieved item meets the relevance threshold.
    When averaged across all queries, yields Mean Reciprocal Rank (MRR).
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
    Computes Discounted Cumulative Gain (DCG@K) using graded exponential relevance gain:
    $$\\text{DCG}@K = \\sum_{i=1}^K \\frac{2^{\\text{rel}_i} - 1}{\\log_2(i + 1)}$$
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
    Computes Normalized Discounted Cumulative Gain (NDCG@K):
    $$\\text{NDCG}@K = \\frac{\\text{DCG}@K}{\\text{IDCG}@K}$$
    Where $\\text{IDCG}@K$ is the maximum possible DCG obtained by sorting all candidate items
    in descending order of their true relevance grades.
    Returns 0.0 if $\\text{IDCG}@K = 0$.
    """
    actual_dcg = compute_dcg_at_k(ranked_tutor_ids, query_qrels, k)

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
    ranked_items: List[Dict[str, Any]],
    query_qrels: Dict[str, int],
) -> Optional[float]:
    """
    Computes Pairwise Ranking Accuracy (Kendall tau concordance ratio):
    For all pairs $(A, B)$ where ground-truth $\\text{Grade}(A) > \\text{Grade}(B)$:
    - Concordant ($\\text{Score}(A) > \\text{Score}(B)$) -> 1.0
    - Tied ($\\text{Score}(A) == \\text{Score}(B)$) -> 0.5
    - Discordant ($\\text{Score}(A) < \\text{Score}(B)$) -> 0.0
    $$\\text{Accuracy} = \\frac{\\text{Concordant Pairs} + 0.5 \\times \\text{Ties}}{\\text{Total Valid Pairs}}$$
    Returns None if no candidate pairs with distinct relevance grades exist.
    """
    score_map = {item["id"]: item["overall_score"] for item in ranked_items if "id" in item and "overall_score" in item}
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


def compute_all_metrics(
    ranked_items: List[Dict[str, Any]],
    query_qrels: Dict[str, int],
    precision_k: List[int] = PRECISION_K_VALUES,
    recall_k: List[int] = RECALL_K_VALUES,
    ndcg_k: List[int] = NDCG_K_VALUES,
    threshold: int = DEFAULT_RELEVANCE_THRESHOLD,
) -> Dict[str, float]:
    """Computes all evaluation metrics for a single query ranking."""
    ranked_ids = [item["id"] for item in ranked_items if "id" in item]

    metrics: Dict[str, float] = {}

    for k in precision_k:
        metrics[f"precision@{k}"] = compute_precision_at_k(ranked_ids, query_qrels, k=k, relevance_threshold=threshold)

    for k in recall_k:
        metrics[f"recall@{k}"] = compute_recall_at_k(ranked_ids, query_qrels, k=k, relevance_threshold=threshold)

    metrics["mrr"] = compute_mrr(ranked_ids, query_qrels, relevance_threshold=threshold)

    for k in ndcg_k:
        metrics[f"ndcg@{k}"] = compute_ndcg_at_k(ranked_ids, query_qrels, k=k)

    pw_acc = compute_pairwise_ranking_accuracy(ranked_items, query_qrels)
    metrics["pairwise_accuracy"] = pw_acc if pw_acc is not None else 0.0

    return metrics


def aggregate_query_metrics(per_query_metrics: List[Dict[str, Any]]) -> Dict[str, float]:
    """Computes macro-averaged metrics across all evaluated queries."""
    if not per_query_metrics:
        return {}

    metric_keys = [k for k, v in per_query_metrics[0].items() if isinstance(v, (int, float))]
    aggregated = {}

    for key in metric_keys:
        values = [q_m[key] for q_m in per_query_metrics if key in q_m and isinstance(q_m[key], (int, float))]
        aggregated[key] = round(sum(values) / len(values), 4) if values else 0.0

    return aggregated
