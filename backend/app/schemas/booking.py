import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BookingCreate(BaseModel):
    tutor_id: str = Field(..., description="ID of the tutor profile to book")
    learning_need_id: str = Field(..., description="ID of the student's learning need")
    scheduled_date: str = Field(..., description="Date for the session (YYYY-MM-DD)")
    start_time: str = Field(..., description="Start time for the session (HH:MM)")
    duration_minutes: int = Field(60, description="Session duration in minutes (positive integer)")
    student_message: Optional[str] = Field(None, max_length=500, description="Optional note for the tutor")

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Duration must be a positive integer greater than 0.")
        if v > 480:
            raise ValueError("Duration cannot exceed 480 minutes (8 hours).")
        return v

    @field_validator("scheduled_date")
    @classmethod
    def validate_scheduled_date(cls, v: str) -> str:
        s = v.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
            raise ValueError("scheduled_date must be in YYYY-MM-DD format.")
        try:
            datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date supplied for scheduled_date.")
        return s

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: str) -> str:
        s = v.strip()
        if not re.match(r"^\d{1,2}:\d{2}$", s):
            raise ValueError("start_time must be in HH:MM format.")
        parts = s.split(":")
        hours, mins = int(parts[0]), int(parts[1])
        if hours < 0 or hours > 23 or mins < 0 or mins > 59:
            raise ValueError("start_time must be a valid clock time between 00:00 and 23:59.")
        return f"{hours:02d}:{mins:02d}"

    @field_validator("student_message")
    @classmethod
    def validate_message(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip() or None
        return None


class BookingDecision(BaseModel):
    decision: str = Field(..., description="Tutor decision: ACCEPTED or REJECTED")
    reason: Optional[str] = Field(None, max_length=500, description="Optional reason for the decision")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        v_upper = v.upper().strip()
        if v_upper not in ("ACCEPTED", "REJECTED"):
            raise ValueError("Decision must be either ACCEPTED or REJECTED.")
        return v_upper


class BookingCancel(BaseModel):
    reason: Optional[str] = Field(None, max_length=500, description="Reason for cancellation")


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    tutor_id: str
    learning_need_id: str
    learning_need_title: Optional[str] = None
    scheduled_date: str
    start_time: str
    duration_minutes: int
    hourly_rate: float
    total_amount: float
    student_message: Optional[str] = None
    status: str
    tutor_name: Optional[str] = None
    tutor_email: Optional[str] = None
    tutor_location: Optional[str] = None
    tutor_profile_picture_path: Optional[str] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
