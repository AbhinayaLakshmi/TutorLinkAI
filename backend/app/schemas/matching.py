from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class MatchingAvailabilitySlot(BaseModel):
    day: str = Field(..., description="Day of the week (e.g. Monday)")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")

class MatchingBreakdown(BaseModel):
    subject_score: float
    learning_need_score: Optional[float] = None
    semantic_score: Optional[float] = None
    topic_score: Optional[float] = None
    location_score: float
    fee_score: float
    time_score: float
    distance_km: float

class TutorRecommendation(BaseModel):
    id: str
    user_id: str
    name: str
    subjects: List[str]
    bio: Optional[str] = None
    hourly_rate: float
    location: Optional[str] = None
    availability: List[MatchingAvailabilitySlot] = []
    rating: Optional[float] = None
    overall_score: float
    overall_percentage: int
    breakdown: MatchingBreakdown
    learning_need_id: Optional[str] = None
    learning_need_title: Optional[str] = None
    profile_picture_path: Optional[str] = None
    matched_topics: List[str] = Field(default_factory=list, description="Topics matching student needs")
    match_reasons: List[str] = Field(default_factory=list, description="Evidence-grounded recommendation reasons")
    pedagogy_compatibility: Optional[float] = Field(default=None, description="Pedagogical style compatibility score if evidence exists")
    explanation_summary: Optional[str] = Field(default=None, description="Evidence-grounded explanation summary")

    class Config:
        from_attributes = True
        orm_mode = True
