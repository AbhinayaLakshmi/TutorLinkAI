import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.models.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    tutor_id = Column(String(36), ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    learning_need_id = Column(String(36), ForeignKey("learning_needs.id", ondelete="CASCADE"), nullable=False, index=True)

    scheduled_date = Column(String(50), nullable=False)
    start_time = Column(String(50), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    status = Column(String(50), nullable=False, default="SCHEDULED", index=True)  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED

    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    actual_duration_minutes = Column(Integer, nullable=True)
    completion_note = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    booking = relationship("Booking", backref="session", uselist=False)
    student_profile = relationship("StudentProfile", backref="sessions")
    tutor_profile = relationship("TutorProfile", backref="sessions")
    learning_need = relationship("LearningNeed", backref="sessions")
