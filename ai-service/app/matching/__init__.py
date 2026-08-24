"""Matching module exports"""
from .config import (
    DEFAULT_WEIGHT_SUBJECT,
    DEFAULT_WEIGHT_LOCATION,
    DEFAULT_WEIGHT_FEE,
    DEFAULT_WEIGHT_TIME,
    DEFAULT_MAX_RADIUS_KM,
    DEFAULT_FEE_TOLERANCE_RATIO,
    MIN_OVERALL_SCORE_THRESHOLD,
    MODEL_NAME,
)
from .embeddings import EmbeddingService, get_embedding_service
from .scoring import (
    calculate_haversine_distance,
    calculate_location_score,
    calculate_fee_score,
    calculate_time_score,
    calculate_composite_score,
    normalize_scores_minmax,
)
from .matcher import TutorMatcher

__all__ = [
    "DEFAULT_WEIGHT_SUBJECT",
    "DEFAULT_WEIGHT_LOCATION",
    "DEFAULT_WEIGHT_FEE",
    "DEFAULT_WEIGHT_TIME",
    "DEFAULT_MAX_RADIUS_KM",
    "DEFAULT_FEE_TOLERANCE_RATIO",
    "MIN_OVERALL_SCORE_THRESHOLD",
    "MODEL_NAME",
    "EmbeddingService",
    "get_embedding_service",
    "calculate_haversine_distance",
    "calculate_location_score",
    "calculate_fee_score",
    "calculate_time_score",
    "calculate_composite_score",
    "normalize_scores_minmax",
    "TutorMatcher",
]
