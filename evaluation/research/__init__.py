"""
TutorLinkAI — Reproducible ML Recommendation Evaluation Pipeline.
"""
from evaluation.research.config import (
    ResearchConfig,
    MODEL_LEGACY_BASELINE,
    MODEL_DENSE_SEMANTIC,
    MODEL_TOPIC_OVERLAP,
    MODEL_FULL_HYBRID,
    MODEL_FULL_HYBRID_FEEDBACK,
    ALL_MODELS,
)
from evaluation.research.data_loader import BenchmarkDataLoader
from evaluation.research.preprocessing import ResearchPreprocessor
from evaluation.research.models import ResearchModelsEvaluator
from evaluation.research.metrics import (
    compute_precision_at_k,
    compute_recall_at_k,
    compute_mrr,
    compute_dcg_at_k,
    compute_ndcg_at_k,
    compute_pairwise_ranking_accuracy,
    compute_all_metrics,
    aggregate_query_metrics,
)
from evaluation.research.evaluate import ResearchEvaluationEngine
from evaluation.research.run_all_evaluations import run_all_research_evaluations

__all__ = [
    "ResearchConfig",
    "MODEL_LEGACY_BASELINE",
    "MODEL_DENSE_SEMANTIC",
    "MODEL_TOPIC_OVERLAP",
    "MODEL_FULL_HYBRID",
    "MODEL_FULL_HYBRID_FEEDBACK",
    "ALL_MODELS",
    "BenchmarkDataLoader",
    "ResearchPreprocessor",
    "ResearchModelsEvaluator",
    "compute_precision_at_k",
    "compute_recall_at_k",
    "compute_mrr",
    "compute_dcg_at_k",
    "compute_ndcg_at_k",
    "compute_pairwise_ranking_accuracy",
    "compute_all_metrics",
    "aggregate_query_metrics",
    "ResearchEvaluationEngine",
    "run_all_research_evaluations",
]
