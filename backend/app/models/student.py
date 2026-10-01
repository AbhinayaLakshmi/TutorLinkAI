import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, Boolean, DateTime, Numeric
from sqlalchemy.orm import relationship
from backend.app.models.base import Base

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Onboarding Fields
    student_type = Column(String(50), nullable=True)  # SCHOOL, UNIVERSITY
    
    # School specific fields
    school_board = Column(String(100), nullable=True)  # CBSE, Matriculation, ICSE, State Board, Other
    grade = Column(String(50), nullable=True)  # Class 1 through Class 12
    school_name = Column(String(255), nullable=True)
    
    # University specific fields
    university = Column(String(255), nullable=True)
    course = Column(String(255), nullable=True)
    year_of_study = Column(Integer, nullable=True)
    specialization = Column(String(255), nullable=True)
    
    # Both fields
    location = Column(String(255), nullable=True)
    preferred_learning_mode = Column(String(100), nullable=True)  # Online, Offline, Both
    preferred_tutor_languages = Column(JSON, nullable=True)  # List of preferred languages

    # Legacy field wrapper mapping (for compatibility if any)
    @property
    def institution(self):
        return self.school_name if self.student_type == "SCHOOL" else self.university

    # Relationships
    user = relationship("User", back_populates="student_profile")
    requirements = relationship("StudentRequirements", back_populates="student_profile", uselist=False, cascade="all, delete-orphan")
    learning_needs = relationship("LearningNeed", back_populates="student_profile", cascade="all, delete-orphan")


class StudentRequirements(Base):
    __tablename__ = "student_requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    subjects = Column(JSON, nullable=True)  # List of subjects
    topics = Column(JSON, nullable=True)  # List of topics
    learning_goals = Column(Text, nullable=True)
    preferred_tutor_characteristics = Column(Text, nullable=True)
    preferred_availability = Column(Text, nullable=True)
    preferred_learning_mode = Column(String(100), nullable=True)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="requirements")


class LearningNeed(Base):
    __tablename__ = "learning_needs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_profile_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    subjects = Column(JSON, nullable=False)  # List of subjects
    topics = Column(JSON, nullable=True)    # List of topics
    learning_goals = Column(Text, nullable=True)
    preferred_tutor_characteristics = Column(Text, nullable=True)
    preferred_availability = Column(Text, nullable=True)
    budget_min = Column(Numeric(10, 2), nullable=True)
    budget_max = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student_profile = relationship("StudentProfile", back_populates="learning_needs")

