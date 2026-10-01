"""
Research Evaluation Configuration and Constants.
Defines paths, model identifiers, ablation component flags, default parameters, and sweep grids.
"""
from pathlib import Path
from typing import Dict, List, Any

# Root Directory Paths
RESEARCH_DIR = Path(__file__).resolve().parent
REPO_ROOT = RESEARCH_DIR.parent.parent
BENCHMARK_DATA_DIR = REPO_ROOT / "evaluation" / "matching"

# Dataset File Paths (Step 7A Source of Truth)
QUERIES_PATH = BENCHMARK_DATA_DIR / "queries.json"
TUTORS_PATH = BENCHMARK_DATA_DIR / "tutors.json"
QRELS_PATH = BENCHMARK_DATA_DIR / "qrels.json"
FEEDBACK_SCENARIOS_PATH = BENCHMARK_DATA_DIR / "feedback_scenarios.json"

# Output Results Directory
RESULTS_DIR = RESEARCH_DIR / "results"

# Version Metadata
PIPELINE_VERSION = "1.0.0"
DATASET_VERSION = "1.0.0"
METRICS_VERSION = "1.0.0"

# Model Configuration Identifiers
MODEL_LEGACY_BASELINE = "legacy_baseline"
MODEL_DENSE_SEMANTIC = "dense_semantic"
MODEL_TOPIC_OVERLAP = "topic_overlap"
MODEL_FULL_HYBRID = "full_hybrid"
MODEL_FULL_HYBRID_FEEDBACK = "full_hybrid_feedback"

ALL_MODELS = [
    MODEL_LEGACY_BASELINE,
    MODEL_DENSE_SEMANTIC,
    MODEL_TOPIC_OVERLAP,
    MODEL_FULL_HYBRID,
    MODEL_FULL_HYBRID_FEEDBACK,
]

MODEL_DISPLAY_NAMES = {
    MODEL_LEGACY_BASELINE: "Configuration A: Legacy Baseline",
    MODEL_DENSE_SEMANTIC: "Configuration B: Dense Semantic Only",
    MODEL_TOPIC_OVERLAP: "Configuration C: Topic Overlap Only",
    MODEL_FULL_HYBRID: "Configuration D: Full Hybrid Matcher (Production)",
    MODEL_FULL_HYBRID_FEEDBACK: "Configuration E: Full Hybrid + Feedback (Experimental)",
}

# Component Ablation Matrix Definitions
MODEL_COMPONENTS: Dict[str, Dict[str, Any]] = {
    MODEL_LEGACY_BASELINE: {
        "subject_gate": True,
        "semantic_embeddings": False,
        "topic_overlap": False,
        "location_scoring": True,
        "fee_scoring": True,
        "time_scoring": True,
        "bayesian_feedback": False,
        "learning_need_weight": 0.40,
        "location_weight": 0.20,
        "fee_weight": 0.20,
        "time_weight": 0.20,
        "feedback_weight": 0.00,
    },
    MODEL_DENSE_SEMANTIC: {
        "subject_gate": True,
        "semantic_embeddings": True,
        "topic_overlap": False,
        "location_scoring": True,
        "fee_scoring": True,
        "time_scoring": True,
        "bayesian_feedback": False,
        "learning_need_weight": 0.45,
        "location_weight": 0.20,
        "fee_weight": 0.20,
        "time_weight": 0.15,
        "feedback_weight": 0.00,
    },
    MODEL_TOPIC_OVERLAP: {
        "subject_gate": True,
        "semantic_embeddings": False,
        "topic_overlap": True,
        "location_scoring": True,
        "fee_scoring": True,
        "time_scoring": True,
        "bayesian_feedback": False,
        "learning_need_weight": 0.45,
        "location_weight": 0.20,
        "fee_weight": 0.20,
        "time_weight": 0.15,
        "feedback_weight": 0.00,
    },
    MODEL_FULL_HYBRID: {
        "subject_gate": True,
        "semantic_embeddings": True,
        "topic_overlap": True,
        "location_scoring": True,
        "fee_scoring": True,
        "time_scoring": True,
        "bayesian_feedback": False,
        "learning_need_weight": 0.45,
        "location_weight": 0.20,
        "fee_weight": 0.20,
        "time_weight": 0.15,
        "feedback_weight": 0.00,
    },
    MODEL_FULL_HYBRID_FEEDBACK: {
        "subject_gate": True,
        "semantic_embeddings": True,
        "topic_overlap": True,
        "location_scoring": True,
        "fee_scoring": True,
        "time_scoring": True,
        "bayesian_feedback": True,
        "learning_need_weight": 0.45,
        "location_weight": 0.20,
        "fee_weight": 0.20,
        "time_weight": 0.15,
        "feedback_weight": 0.10,
    },
}

# Production Reference Weights (for strict safety assertions)
PROD_WEIGHT_LEARNING_NEED: float = 0.45
PROD_WEIGHT_LOCATION: float = 0.20
PROD_WEIGHT_FEE: float = 0.20
PROD_WEIGHT_TIME: float = 0.15

# Research Experimental Feedback Parameters
DEFAULT_FEEDBACK_WEIGHT: float = 0.10
DEFAULT_SMOOTHING_M: float = 5.0
DEFAULT_GLOBAL_PRIOR: float = 3.5

# Sweep Grids for Sensitivity Analysis
FEEDBACK_WEIGHT_SWEEP: List[float] = [0.00, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
SMOOTHING_M_SWEEP: List[float] = [1.0, 5.0, 10.0, 20.0]

# Metric Configurations
PRECISION_K_VALUES: List[int] = [1, 3, 5]
RECALL_K_VALUES: List[int] = [5]
NDCG_K_VALUES: List[int] = [3, 5]
DEFAULT_RELEVANCE_THRESHOLD: int = 2


class ResearchConfig:
    """Encapsulates execution parameters for a research evaluation run."""
    def __init__(
        self,
        feedback_weight: float = DEFAULT_FEEDBACK_WEIGHT,
        smoothing_m: float = DEFAULT_SMOOTHING_M,
        global_prior: float = DEFAULT_GLOBAL_PRIOR,
        relevance_threshold: int = DEFAULT_RELEVANCE_THRESHOLD,
    ):
        self.feedback_weight = feedback_weight
        self.smoothing_m = smoothing_m
        self.global_prior = global_prior
        self.relevance_threshold = relevance_threshold
        self.results_dir = RESULTS_DIR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_version": PIPELINE_VERSION,
            "dataset_version": DATASET_VERSION,
            "metrics_version": METRICS_VERSION,
            "feedback_weight": self.feedback_weight,
            "smoothing_m": self.smoothing_m,
            "global_prior": self.global_prior,
            "relevance_threshold": self.relevance_threshold,
            "models_evaluated": ALL_MODELS,
        }
