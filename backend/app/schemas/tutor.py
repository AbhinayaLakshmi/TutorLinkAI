from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class EducationSchema(BaseModel):
    highest_degree: str = Field(..., min_length=1)
    degree_name: str = Field(..., min_length=1)
    university: str = Field(..., min_length=1)
    specialization: Optional[str] = None
    graduation_year: int = Field(..., ge=1900, le=2100, description="Graduation year must be between 1900 and 2100")

    class Config:
        from_attributes = True
        orm_mode = True

class TutorExpertiseSchema(BaseModel):
    subjects_taught: List[str] = Field(default_factory=list)
    topics_expertise: List[str] = Field(default_factory=list)
    student_levels: List[str] = Field(default_factory=list)
    years_of_experience: int = Field(..., ge=0, description="Years of experience cannot be negative")
    previous_experience: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    languages_can_teach_in: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True
        orm_mode = True

class TimeRangeSchema(BaseModel):
    start: str = Field(..., description="Start time in HH:MM format")
    end: str = Field(..., description="End time in HH:MM format")

    @field_validator("start", "end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("Time must be in HH:MM format")
        h, m = parts
        try:
            h_int = int(h)
            m_int = int(m)
        except ValueError:
            raise ValueError("Time values must be digits")
        if not (0 <= h_int < 24) or not (0 <= m_int < 60):
            raise ValueError("Invalid hour or minute")
        return v

class AvailabilitySchema(BaseModel):
    day_of_week: str = Field(..., description="Day of the week (e.g. Monday)")
    time_ranges: List[TimeRangeSchema] = Field(default_factory=list)
    preferred_session_duration: int = Field(60, ge=15, le=480, description="Duration in minutes, between 15 and 480")
    hourly_rate: float = Field(..., ge=0.0, description="Hourly rate must be a non-negative number")

    @field_validator("day_of_week")
    @classmethod
    def validate_day(cls, v: str) -> str:
        valid_days = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
        if v.lower() not in valid_days:
            raise ValueError("Invalid day of week")
        return v.capitalize()

    class Config:
        from_attributes = True
        orm_mode = True

class CertificateOutSchema(BaseModel):
    id: str
    original_filename: str
    file_type: str
    file_size: int
    upload_timestamp: datetime
    verification_status: str

    class Config:
        from_attributes = True
        orm_mode = True

class TutorProfileUpdate(BaseModel):
    location: Optional[str] = None
    languages_spoken: List[str] = Field(default_factory=list)
    preferred_teaching_mode: Optional[str] = None
    education: Optional[List[EducationSchema]] = None
    expertise: Optional[TutorExpertiseSchema] = None
    availability: Optional[List[AvailabilitySchema]] = None

class TutorProfileOut(BaseModel):
    id: str
    user_id: str
    profile_picture_path: Optional[str] = None
    location: Optional[str] = None
    languages_spoken: Optional[List[str]] = None
    preferred_teaching_mode: Optional[str] = None
    verification_status: str
    education: List[EducationSchema] = Field(default_factory=list)
    expertise: Optional[TutorExpertiseSchema] = None
    availability: List[AvailabilitySchema] = Field(default_factory=list)
    certificates: List[CertificateOutSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True
        orm_mode = True
