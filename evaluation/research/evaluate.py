"""
Evaluation Engine for Reproducible Research Benchmark.
Coordinates running all 5 models, generating per-query rankings, computing aggregate metrics,
and executing ablation matrices.
"""
from typing import Dict, List, Any, Optional

from evaluation.research.config import (
    ResearchConfig,
    ALL_MODELS,
    MODEL_DISPLAY_NAMES,
    MODEL_COMPONENTS,
    FEEDBACK_WEIGHT_SWEEP,
    SMOOTHING_M_SWEEP,
)
from evaluation.research.models import ResearchModelsEvaluator
from evaluation.research.metrics import (
    compute_all_metrics,
    aggregate_query_metrics,
)


class ResearchEvaluationEngine:
    """Coordinates multi-model benchmark evaluation, ablation, and metric aggregation."""

    def __init__(
        self,
        config: Optional[ResearchConfig] = None,
        models_evaluator: Optional[ResearchModelsEvaluator] = None,
    ):
        self.config = config or ResearchConfig()
        self.models_evaluator = models_evaluator or ResearchModelsEvaluator()

    def evaluate_dataset(
        self,
        queries: List[Dict[str, Any]],
        tutors: List[Dict[str, Any]],
        qrels: Dict[str, Dict[str, int]],
    ) -> Dict[str, Any]:
        """
        Runs all 5 model configurations against all queries in the dataset.
        Returns complete ranking outputs and macro-averaged metrics.
        """
        model_rankings: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
            m: {} for m in ALL_MODELS
        }
        per_query_metrics: Dict[str, List[Dict[str, Any]]] = {
            m: [] for m in ALL_MODELS
        }

        for query in queries:
            q_id = query["query_id"]
            query_qrels = qrels.get(q_id, {})

            for model_name in ALL_MODELS:
                ranked = self.models_evaluator.evaluate_model(
                    model_name=model_name,
                    query=query,
                    candidate_tutors=tutors,
                    feedback_weight=self.config.feedback_weight,
                    smoothing_m=self.config.smoothing_m,
                    global_prior=self.config.global_prior,
                )
                model_rankings[model_name][q_id] = ranked

                q_metrics = compute_all_metrics(
                    ranked_items=ranked,
                    query_qrels=query_qrels,
                    threshold=self.config.relevance_threshold,
                )
                q_metrics_record = dict(q_metrics)
                q_metrics_record["query_id"] = q_id
                per_query_metrics[model_name].append(q_metrics_record)

        # Compute macro-aggregated metrics
        aggregated_metrics: Dict[str, Dict[str, float]] = {}
        for model_name in ALL_MODELS:
            aggregated_metrics[model_name] = aggregate_query_metrics(
                per_query_metrics[model_name]
            )

        return {
            "config": self.config.to_dict(),
            "model_rankings": model_rankings,
            "per_query_metrics": per_query_metrics,
            "aggregated_metrics": aggregated_metrics,
        }

    def build_ablation_summary(
        self, aggregated_metrics: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """Constructs comparative ablation matrix with component inclusion flags and metrics."""
        summary_rows = []
        for model_name in ALL_MODELS:
            components = MODEL_COMPONENTS.get(model_name, {})
            metrics = aggregated_metrics.get(model_name, {})

            row = {
                "model_id": model_name,
                "display_name": MODEL_DISPLAY_NAMES.get(model_name, model_name),
                "subject_gate": components.get("subject_gate", False),
                "semantic_embeddings": components.get("semantic_embeddings", False),
                "topic_overlap": components.get("topic_overlap", False),
                "location_scoring": components.get("location_scoring", False),
                "fee_scoring": components.get("fee_scoring", False),
                "time_scoring": components.get("time_scoring", False),
                "bayesian_feedback": components.get("bayesian_feedback", False),
                "feedback_weight": components.get("feedback_weight", 0.0),
                "precision@1": metrics.get("precision@1", 0.0),
                "precision@3": metrics.get("precision@3", 0.0),
                "precision@5": metrics.get("precision@5", 0.0),
                "recall@5": metrics.get("recall@5", 0.0),
                "mrr": metrics.get("mrr", 0.0),
                "ndcg@3": metrics.get("ndcg@3", 0.0),
                "ndcg@5": metrics.get("ndcg@5", 0.0),
                "pairwise_accuracy": metrics.get("pairwise_accuracy", 0.0),
            }
            summary_rows.append(row)

        return summary_rows
