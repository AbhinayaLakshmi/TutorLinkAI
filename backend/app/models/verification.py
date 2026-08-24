import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, JSON, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tutor_profile_id = Column(String(36), ForeignKey("tutor_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    certificate_id = Column(String(36), ForeignKey("certificates.id", ondelete="CASCADE"), nullable=False)
    
    # Process Statuses
    verification_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, PROCESSING, VERIFIED, FAILED, MANUAL_REVIEW
    ocr_status = Column(String(50), nullable=False, default="PENDING")           # PENDING, PROCESSING, COMPLETED, FAILED
    certificate_validation_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, MATCH, PARTIAL_MATCH, MISMATCH, INSUFFICIENT_DATA
    security_analysis_status = Column(String(50), nullable=False, default="NOT_AVAILABLE")
    university_verification_status = Column(String(50), nullable=False, default="NOT_AVAILABLE")
    face_verification_status = Column(String(50), nullable=False, default="NOT_AVAILABLE")
    liveness_status = Column(String(50), nullable=False, default="NOT_AVAILABLE")
    
    # Validation Results
    overall_result = Column(String(50), nullable=False, default="PENDING")
    failure_reason = Column(Text, nullable=True)
    manual_review_required = Column(Boolean, default=False, nullable=False)
    
    # Extracted data cache
    ocr_metadata = Column(JSON, nullable=True)  # {name: str, university: str, degree: str, year: int, confidence: float}
    security_analysis_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    tutor_profile = relationship("TutorProfile", backref="verification_record")
    certificate = relationship("Certificate", backref="verification_records")
