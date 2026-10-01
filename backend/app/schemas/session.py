from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SessionStart(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SessionComplete(BaseModel):
    completion_note: Optional[str] = Field(None, max_length=2000, description="Optional note or summary upon session completion")
    model_config = ConfigDict(from_attributes=True)


class SessionCancel(BaseModel):
    reason: Optional[str] = Field(None, max_length=500, description="Reason for cancelling the session")
    model_config = ConfigDict(from_attributes=True)


class SessionOut(BaseModel):
    id: str
    booking_id: str
    student_id: str
    tutor_id: str
    learning_need_id: str
    learning_need_title: Optional[str] = None
    scheduled_date: str
    start_time: str
    duration_minutes: int
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    completion_note: Optional[str] = None
    cancellation_reason: Optional[str] = None

    tutor_name: Optional[str] = None
    tutor_email: Optional[str] = None
    tutor_location: Optional[str] = None
    tutor_profile_picture_path: Optional[str] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
