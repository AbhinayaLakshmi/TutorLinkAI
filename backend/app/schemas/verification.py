from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class VerificationRecordOut(BaseModel):
    id: str
    tutor_profile_id: str
    certificate_id: str
    verification_status: str
    ocr_status: str
    certificate_validation_status: str
    security_analysis_status: str
    university_verification_status: str
    face_verification_status: str
    liveness_status: str
    overall_result: str
    failure_reason: Optional[str] = None
    manual_review_required: bool
    ocr_metadata: Optional[Dict[str, Any]] = None
    security_analysis_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True

class VerificationStatusOut(BaseModel):
    verification_status: str
    overall_result: str
    manual_review_required: bool
    ocr_status: str
    certificate_validation_status: str
