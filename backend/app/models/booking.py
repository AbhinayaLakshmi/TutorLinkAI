import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Numeric
from sqlalchemy.orm import relationship
from backend.app.models.base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    tutor_id = Column(String(36), ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    learning_need_id = Column(String(36), ForeignKey("learning_needs.id", ondelete="CASCADE"), nullable=False, index=True)

    scheduled_date = Column(String(50), nullable=False)
    start_time = Column(String(50), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    hourly_rate = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    student_message = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="PENDING", index=True)  # PENDING, CONFIRMED, REJECTED, CANCELLED

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    student_profile = relationship("StudentProfile", backref="bookings")
    tutor_profile = relationship("TutorProfile", backref="bookings")
    learning_need = relationship("LearningNeed", backref="bookings")
