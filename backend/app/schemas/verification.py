from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class VerificationRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class VerificationStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verification_status: str
    overall_result: str
    manual_review_required: bool
    ocr_status: str
    certificate_validation_status: str


class VerificationReviewCreate(BaseModel):
    decision: str = Field(..., description="APPROVED, REJECTED, or RESUBMISSION_REQUESTED")
    reason: Optional[str] = Field(None, description="Reason for decision, required for REJECTED and RESUBMISSION_REQUESTED")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: str) -> str:
        v_upper = v.upper().strip()
        if v_upper not in ("APPROVED", "REJECTED", "RESUBMISSION_REQUESTED"):
            raise ValueError("Decision must be APPROVED, REJECTED, or RESUBMISSION_REQUESTED")
        return v_upper

    @model_validator(mode="after")
    def check_reason_required(self):
        if self.decision in ("REJECTED", "RESUBMISSION_REQUESTED"):
            if not self.reason or not self.reason.strip():
                raise ValueError(f"Reason is required when decision is {self.decision}")
        return self


class VerificationReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    verification_record_id: str
    reviewer_id: str
    reviewer_name: Optional[str] = None
    decision: str
    reason: Optional[str] = None
    created_at: datetime


class ManualReviewQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tutor_profile_id: str
    tutor_name: str
    tutor_email: str
    certificate_id: str
    certificate_filename: str
    verification_status: str
    manual_review_required: bool
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ManualReviewDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verification_record: VerificationRecordOut
    tutor: Dict[str, Any]
    certificate: Dict[str, Any]
    review_history: List[VerificationReviewOut]
