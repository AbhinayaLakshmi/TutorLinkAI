from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class StudentRequirementsSchema(BaseModel):
    subjects: Optional[List[str]] = Field(default_factory=list)
    topics: Optional[List[str]] = Field(default_factory=list)
    learning_goals: Optional[str] = None
    preferred_tutor_characteristics: Optional[str] = None
    preferred_availability: Optional[str] = None

    class Config:
        from_attributes = True
        orm_mode = True

class LearningNeedCreate(BaseModel):
    title: str = Field(..., min_length=1)
    subjects: List[str] = Field(..., min_length=1)
    topics: Optional[List[str]] = Field(default_factory=list)
    learning_goals: Optional[str] = None
    preferred_tutor_characteristics: Optional[str] = None
    preferred_availability: Optional[str] = None
    budget_min: Optional[float] = Field(None, ge=0, description="Minimum hourly budget")
    budget_max: Optional[float] = Field(None, ge=0, description="Maximum hourly budget")
    is_active: Optional[bool] = False

    @model_validator(mode="after")
    def validate_budget_range(self):
        if self.budget_min is not None and self.budget_min < 0:
            raise ValueError("budget_min cannot be negative")
        if self.budget_max is not None and self.budget_max < 0:
            raise ValueError("budget_max cannot be negative")
        if self.budget_min is not None and self.budget_max is not None and self.budget_max < self.budget_min:
            raise ValueError("budget_max cannot be less than budget_min")
        return self


class LearningNeedUpdate(BaseModel):
    title: Optional[str] = None
    subjects: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    learning_goals: Optional[str] = None
    preferred_tutor_characteristics: Optional[str] = None
    preferred_availability: Optional[str] = None
    budget_min: Optional[float] = Field(None, ge=0, description="Minimum hourly budget")
    budget_max: Optional[float] = Field(None, ge=0, description="Maximum hourly budget")
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_budget_range(self):
        if self.budget_min is not None and self.budget_min < 0:
            raise ValueError("budget_min cannot be negative")
        if self.budget_max is not None and self.budget_max < 0:
            raise ValueError("budget_max cannot be negative")
        if self.budget_min is not None and self.budget_max is not None and self.budget_max < self.budget_min:
            raise ValueError("budget_max cannot be less than budget_min")
        return self


class LearningNeedOut(BaseModel):
    id: str
    student_profile_id: str
    title: str
    subjects: List[str]
    topics: Optional[List[str]] = None
    learning_goals: Optional[str] = None
    preferred_tutor_characteristics: Optional[str] = None
    preferred_availability: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True

class StudentProfileUpdate(BaseModel):
    student_type: str = Field(..., description="Must be SCHOOL or UNIVERSITY")
    
    # School specific
    school_board: Optional[str] = None
    grade: Optional[str] = None
    school_name: Optional[str] = None
    
    # University specific
    university: Optional[str] = None
    course: Optional[str] = None
    year_of_study: Optional[int] = Field(None, ge=1, le=10)
    specialization: Optional[str] = None
    
    # Both
    location: str = Field(..., min_length=1)
    preferred_learning_mode: str = Field(..., description="Must be Online, Offline, or Both")
    preferred_tutor_languages: List[str] = Field(default_factory=list)
    
    requirements: Optional[StudentRequirementsSchema] = None

    @field_validator("student_type")
    @classmethod
    def validate_student_type(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ("SCHOOL", "UNIVERSITY"):
            raise ValueError("student_type must be either SCHOOL or UNIVERSITY")
        return v_upper

    @field_validator("preferred_learning_mode")
    @classmethod
    def validate_learning_mode(cls, v: str) -> str:
        v_cap = v.capitalize()
        if v.lower() not in ("online", "offline", "both"):
            raise ValueError("preferred_learning_mode must be Online, Offline, or Both")
        return v_cap

class StudentProfileOut(BaseModel):
    id: str
    user_id: str
    student_type: Optional[str] = None
    school_board: Optional[str] = None
    grade: Optional[str] = None
    school_name: Optional[str] = None
    university: Optional[str] = None
    course: Optional[str] = None
    year_of_study: Optional[int] = None
    specialization: Optional[str] = None
    location: Optional[str] = None
    preferred_learning_mode: Optional[str] = None
    preferred_tutor_languages: Optional[List[str]] = None
    requirements: Optional[StudentRequirementsSchema] = None
    learning_needs: Optional[List[LearningNeedOut]] = None

    class Config:
        from_attributes = True
        orm_mode = True

