from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.matching import TutorMatcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-matching-service")

app = FastAPI(
    title="TutorLinkAI Matching Service",
    description="AI-powered Tutor Matching and Recommendation Service",
    version="1.0.0"
)

# Instantiate TutorMatcher once
try:
    matcher = TutorMatcher()
    logger.info("TutorMatcher initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize TutorMatcher: {e}")
    matcher = None

# Safe conversion function for Pydantic V1/V2 compatibility
def to_dict(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj.dict()

# Pydantic validation schemas
class StudentQuerySchema(BaseModel):
    subjects_needed: str = Field(..., description="Subject(s) the student needs help with")
    latitude: float = Field(13.0827, description="Student latitude coordinates")
    longitude: float = Field(80.2707, description="Student longitude coordinates")
    budget_min: float = Field(300.0, description="Minimum budget")
    budget_max: float = Field(1000.0, description="Maximum budget")
    preferred_slots: List[Dict[str, Any]] = Field(default_factory=list, description="Preferred availability slots")
    topics: Optional[List[str]] = Field(default_factory=list, description="List of topics needed")
    topics_needed: Optional[List[str]] = Field(default=None, description="Alias for topics")
    learning_goals: Optional[str] = Field(default=None, description="Specific learning goals / outcomes")
    preferred_tutor_characteristics: Optional[str] = Field(default=None, description="Preferred teaching style / tutor characteristics")
    preferred_style: Optional[str] = Field(default=None, description="Alias for preferred_tutor_characteristics")
    student_level: Optional[str] = Field(default=None, description="Student academic level (e.g. undergraduate, high school)")
    preferred_learning_mode: Optional[str] = Field(default=None, description="Online, Offline, or Both")
    preferred_mode: Optional[str] = Field(default=None, description="Alias for preferred_learning_mode")
    preferred_tutor_languages: Optional[List[str]] = Field(default_factory=list, description="Preferred languages")
    languages: Optional[List[str]] = Field(default=None, description="Alias for preferred_tutor_languages")
    learning_need_id: Optional[str] = Field(default=None, description="ID of specific learning need if provided")
    learning_need_title: Optional[str] = Field(default=None, description="Title of specific learning need if provided")

class CandidateTutorSchema(BaseModel):
    id: str
    user_id: str
    name: str
    subjects: List[str]
    bio: Optional[str] = None
    hourly_rate: float
    latitude: float
    longitude: float
    area_name: Optional[str] = None
    availability: List[Dict[str, Any]] = Field(default_factory=list)
    rating: Optional[float] = 4.5
    topics_expertise: Optional[List[str]] = Field(default_factory=list, description="Tutor's specific topic areas")
    skills: Optional[List[str]] = Field(default_factory=list, description="Teaching skills, pedagogical methods, strengths")
    student_levels: Optional[List[str]] = Field(default_factory=list, description="Levels tutor can teach")
    languages_can_teach_in: Optional[List[str]] = Field(default_factory=list, description="Languages spoken / can teach in")
    languages: Optional[List[str]] = Field(default=None, description="Alias for languages_can_teach_in")
    preferred_teaching_mode: Optional[str] = Field(default=None, description="Online, Offline, or Both")
    teaching_mode: Optional[str] = Field(default=None, description="Alias for preferred_teaching_mode")
    years_of_experience: Optional[int] = Field(default=0, description="Years of teaching experience")
    is_verified: Optional[bool] = Field(default=True, description="Verification status flag")

class MatchRequest(BaseModel):
    student_query: StudentQuerySchema
    candidate_tutors: List[CandidateTutorSchema]
    weight_learning_need: Optional[float] = None
    weight_subject: Optional[float] = None
    weight_location: Optional[float] = None
    weight_fee: Optional[float] = None
    weight_time: Optional[float] = None
    max_radius_km: Optional[float] = None
    fee_tolerance_ratio: Optional[float] = None
    min_threshold: Optional[float] = None
    use_minmax_normalization: Optional[bool] = False
    top_n: Optional[int] = 10

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "TutorLinkAI AI Matching Service"
    }

@app.get("/health")
def health_check():
    if matcher is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TutorMatcher failed to initialize."
        )
    return {
        "status": "healthy",
        "model_loaded": True
    }

@app.post("/match", status_code=status.HTTP_200_OK)
def match_tutors(request: MatchRequest):
    if matcher is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TutorMatcher is not initialized."
        )

    try:
        # Convert request models to plain dictionaries
        student_query_dict = to_dict(request.student_query)
        candidate_tutors_list = [to_dict(t) for t in request.candidate_tutors]

        # Extract optional params, only pass them if provided (not None)
        kwargs = {}
        optional_params = [
            "weight_learning_need", "weight_subject", "weight_location", "weight_fee", "weight_time",
            "max_radius_km", "fee_tolerance_ratio", "min_threshold",
            "use_minmax_normalization", "top_n"
        ]
        for param in optional_params:
            val = getattr(request, param)
            if val is not None:
                kwargs[param] = val

        # Invoke core ranker algorithm
        ranked_results = matcher.rank_tutors(
            student_query=student_query_dict,
            candidate_tutors=candidate_tutors_list,
            **kwargs
        )

        return ranked_results

    except Exception as e:
        logger.exception("Error occurred during tutor matching process")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during matching: {str(e)}"
        )
