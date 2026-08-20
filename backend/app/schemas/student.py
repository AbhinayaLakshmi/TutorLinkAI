from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class StudentRequirementsSchema(BaseModel):
    subjects: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    learning_goals: Optional[str] = None
    preferred_tutor_characteristics: Optional[str] = None
    preferred_availability: Optional[str] = None

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

    class Config:
        from_attributes = True
        orm_mode = True
