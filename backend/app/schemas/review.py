from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field, ConfigDict


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    review_text: Optional[str] = Field(None, max_length=2000, description="Optional feedback or review notes")


class ReviewOut(BaseModel):
    id: str
    session_id: str
    student_id: str
    tutor_id: str
    rating: int
    review_text: Optional[str] = None
    student_name: Optional[str] = None
    tutor_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TutorReviewSummary(BaseModel):
    average_rating: float = Field(..., description="Average star rating (0.0 - 5.0)")
    total_reviews: int = Field(..., description="Total number of reviews received")
    rating_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
        description="Count of reviews per rating star"
    )

    model_config = ConfigDict(from_attributes=True)
