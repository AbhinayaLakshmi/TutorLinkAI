"""
Feedback & Reputation Scoring Service for TutorLinkAI.

Implements Bayesian shrinkage and review-volume evidence confidence scoring:
- Addresses cold-start for new tutors (neutral prior, no unfair penalty)
- Smooths low-volume ratings toward the global empirical prior
- Provides monotonic asymptotic confidence scaling in [0, 1)
- Keeps feedback scoring isolated and research-ready without affecting live production matching.
"""
from typing import Optional, Dict, Any, List

try:
    from sqlalchemy.orm import Session
    from sqlalchemy import func
    from backend.app.models.review import Review
    HAS_SQLALCHEMY = True
except ImportError:
    Session = Any  # type: ignore
    func = None  # type: ignore
    Review = None  # type: ignore
    HAS_SQLALCHEMY = False


DEFAULT_SMOOTHING_M = 5.0
DEFAULT_GLOBAL_PRIOR = 3.5
MIN_RATING = 1.0
MAX_RATING = 5.0


def calculate_feedback_signal(
    average_rating: Optional[float],
    review_count: int,
    smoothing_m: float = DEFAULT_SMOOTHING_M,
    global_prior: float = DEFAULT_GLOBAL_PRIOR,
    min_rating: float = MIN_RATING,
    max_rating: float = MAX_RATING,
) -> Dict[str, Any]:
    """
    Computes a research-grade Bayesian adjusted rating and review-evidence confidence.

    Formulation:
      n = review_count
      m = smoothing_m (pseudocount confidence weight)
      adjusted_rating = (n / (n + m)) * avg_rating + (m / (n + m)) * global_prior
      confidence = n / (n + m)
      feedback_score = (adjusted_rating - min_rating) / (max_rating - min_rating)

    Properties:
      - When n = 0: adjusted_rating = global_prior, confidence = 0.0, feedback_score in [0, 1]
      - When n is small: rating is shrunk toward global_prior
      - When n is large: adjusted_rating approaches avg_rating, confidence approaches 1.0
      - Deterministic and bounded: confidence in [0, 1], feedback_score in [0, 1]
    """
    n = max(0, int(review_count))
    m = max(1e-6, float(smoothing_m))
    prior = float(global_prior)
    rating_range = max(1e-6, float(max_rating - min_rating))

    if n == 0 or average_rating is None:
        has_reviews = False
        adjusted_rating = prior
        confidence = 0.0
        feedback_score = (prior - min_rating) / rating_range
        feedback_score = max(0.0, min(1.0, feedback_score))
        return {
            "feedback_score": round(feedback_score, 4),
            "average_rating": None,
            "review_count": 0,
            "adjusted_rating": round(adjusted_rating, 4),
            "confidence": 0.0,
            "has_reviews": False,
            "global_prior_used": round(prior, 4),
            "smoothing_m_used": round(m, 2),
        }

    has_reviews = True
    clamped_avg = max(min_rating, min(max_rating, float(average_rating)))
    
    # Bayesian shrinkage weight
    w = n / (n + m)
    adjusted_rating = (w * clamped_avg) + ((1.0 - w) * prior)
    confidence = w
    feedback_score = (adjusted_rating - min_rating) / rating_range
    feedback_score = max(0.0, min(1.0, feedback_score))

    return {
        "feedback_score": round(feedback_score, 4),
        "average_rating": round(clamped_avg, 2),
        "review_count": n,
        "adjusted_rating": round(adjusted_rating, 4),
        "confidence": round(confidence, 4),
        "has_reviews": True,
        "global_prior_used": round(prior, 4),
        "smoothing_m_used": round(m, 2),
    }


def compute_global_review_prior(db: Session, default_prior: float = DEFAULT_GLOBAL_PRIOR) -> float:
    """
    Computes the empirical mean rating across all reviews in the database.
    Falls back to default_prior if no reviews exist.
    """
    result = db.query(func.avg(Review.rating), func.count(Review.id)).first()
    if result and result[1] and result[1] > 0 and result[0] is not None:
        return float(result[0])
    return float(default_prior)


def get_tutor_feedback_signal(
    db: Session,
    tutor_profile_id: str,
    smoothing_m: float = DEFAULT_SMOOTHING_M,
    global_prior: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes the feedback signal for a tutor from active database reviews.
    """
    if global_prior is None:
        global_prior = compute_global_review_prior(db)

    reviews = db.query(Review).filter(Review.tutor_id == tutor_profile_id).all()
    count = len(reviews)
    avg_rating = (sum(r.rating for r in reviews) / count) if count > 0 else None

    return calculate_feedback_signal(
        average_rating=avg_rating,
        review_count=count,
        smoothing_m=smoothing_m,
        global_prior=global_prior,
    )
