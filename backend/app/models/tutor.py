import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class TutorProfile(Base):
    __tablename__ = "tutor_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    profile_picture_path = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    languages_spoken = Column(JSON, nullable=True)
    preferred_teaching_mode = Column(String(100), nullable=True)
    verification_status = Column(String(50), nullable=False, default="PENDING")  # PENDING, VERIFIED, REJECTED
    verification_timestamp = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="tutor_profile")
    education = relationship("Education", back_populates="tutor_profile", cascade="all, delete-orphan")
    expertise = relationship("TutorExpertise", back_populates="tutor_profile", uselist=False, cascade="all, delete-orphan")
    availability = relationship("Availability", back_populates="tutor_profile", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="tutor_profile", cascade="all, delete-orphan")


class Education(Base):
    __tablename__ = "education"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tutor_profile_id = Column(String(36), ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False)
    highest_degree = Column(String(255), nullable=False)
    degree_name = Column(String(255), nullable=False)
    university = Column(String(255), nullable=False)
    specialization = Column(String(255), nullable=True)
    graduation_year = Column(Integer, nullable=False)

    # Relationships
    tutor_profile = relationship("TutorProfile", back_populates="education")


class TutorExpertise(Base):
    __tablename__ = "tutor_expertise"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tutor_profile_id = Column(String(36), ForeignKey("tutor_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    subjects_taught = Column(JSON, nullable=True)  # List of subjects
    topics_expertise = Column(JSON, nullable=True)  # List of topics
    student_levels = Column(JSON, nullable=True)  # List of levels (e.g. primary, secondary, university)
    years_of_experience = Column(Integer, nullable=False, default=0)
    previous_experience = Column(Text, nullable=True)
    skills = Column(JSON, nullable=True)  # List of skill keywords
    languages_can_teach_in = Column(JSON, nullable=True)  # List of languages

    # Relationships
    tutor_profile = relationship("TutorProfile", back_populates="expertise")


class Availability(Base):
    __tablename__ = "availability"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tutor_profile_id = Column(String(36), ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(String(50), nullable=False)  # Monday, Tuesday, etc.
    time_ranges = Column(JSON, nullable=True)  # List of {"start": "HH:MM", "end": "HH:MM"}
    preferred_session_duration = Column(Integer, nullable=False, default=60)  # minutes
    hourly_rate = Column(Float, nullable=False, default=0.0)

    # Relationships
    tutor_profile = relationship("TutorProfile", back_populates="availability")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tutor_profile_id = Column(String(36), ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    verification_status = Column(String(50), nullable=False, default="PENDING")  # PENDING

    # Relationships
    tutor_profile = relationship("TutorProfile", back_populates="certificates")
