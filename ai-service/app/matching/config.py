"""
Configuration settings and constants for AI Matching Service.
All weights and scoring thresholds are defined here as named constants.
"""
import os

# Default Matching Weights for Stage 2 Ranking (must sum to 1.0)
DEFAULT_WEIGHT_SUBJECT: float = float(os.getenv("WEIGHT_SUBJECT", 0.40))
DEFAULT_WEIGHT_LOCATION: float = float(os.getenv("WEIGHT_LOCATION", 0.20))
DEFAULT_WEIGHT_FEE: float = float(os.getenv("WEIGHT_FEE", 0.20))
DEFAULT_WEIGHT_TIME: float = float(os.getenv("WEIGHT_TIME", 0.20))

# Scoring Parameters & Thresholds
DEFAULT_MAX_RADIUS_KM: float = float(os.getenv("MAX_LOCATION_RADIUS_KM", 15.0))
# Fraction of budget range/bounds to allow linear decay before reaching 0.0
DEFAULT_FEE_TOLERANCE_RATIO: float = float(os.getenv("FEE_TOLERANCE_RATIO", 0.35))
# Minimum overall score for candidate to appear in results
MIN_OVERALL_SCORE_THRESHOLD: float = float(os.getenv("MIN_MATCH_THRESHOLD", 0.05))

# Stage 1 Subject Eligibility Threshold (Sentence Transformers fallback on tags)
SUBJECT_GATE_SIMILARITY_THRESHOLD: float = float(os.getenv("SUBJECT_GATE_SIMILARITY_THRESHOLD", 0.75))

# Model Configuration
MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
EARTH_RADIUS_KM: float = 6371.0
