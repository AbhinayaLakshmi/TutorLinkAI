import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=True)
    role = Column(String(50), nullable=False)  # STUDENT, TUTOR
    onboarding_status = Column(String(50), nullable=False, default="INCOMPLETE")  # INCOMPLETE, COMPLETED
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tutor_profile = relationship("TutorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    otp_verification = relationship("OTPVerification", back_populates="user", uselist=False, cascade="all, delete-orphan")


class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    hashed_otp = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    last_sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="otp_verification")
