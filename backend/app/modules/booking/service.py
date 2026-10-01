import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from backend.app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ResourceNotFoundException,
    RoleForbiddenException,
)
from backend.app.models.user import User
from backend.app.models.student import StudentProfile, LearningNeed
from backend.app.models.tutor import TutorProfile, Availability
from backend.app.models.booking import Booking
from backend.app.schemas.booking import BookingCreate

logger = logging.getLogger("booking_service")


def _format_booking_out(booking: Booking) -> Dict[str, Any]:
    """Helper to assemble rich display metadata for BookingOut responses."""
    tutor_profile = booking.tutor_profile
    tutor_user = tutor_profile.user if tutor_profile else None

    student_profile = booking.student_profile
    student_user = student_profile.user if student_profile else None

    learning_need = booking.learning_need

    return {
        "id": booking.id,
        "student_id": booking.student_id,
        "tutor_id": booking.tutor_id,
        "learning_need_id": booking.learning_need_id,
        "learning_need_title": learning_need.title if learning_need else None,
        "scheduled_date": booking.scheduled_date,
        "start_time": booking.start_time,
        "duration_minutes": booking.duration_minutes,
        "hourly_rate": float(booking.hourly_rate),
        "total_amount": float(booking.total_amount),
        "student_message": booking.student_message,
        "status": booking.status,
        "tutor_name": tutor_user.full_name if tutor_user else "Tutor",
        "tutor_email": tutor_user.email if tutor_user else None,
        "tutor_location": tutor_profile.location if tutor_profile else None,
        "tutor_profile_picture_path": tutor_profile.profile_picture_path if tutor_profile else None,
        "student_name": student_user.full_name if student_user else "Student",
        "student_email": student_user.email if student_user else None,
        "created_at": booking.created_at,
        "updated_at": booking.updated_at,
    }


def create_booking(db: Session, student_user: User, payload: BookingCreate) -> Dict[str, Any]:
    # 1. Authenticate & retrieve student profile
    student_profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == student_user.id)
        .first()
    )
    if not student_profile:
        raise BadRequestException("Student profile not found. Please complete onboarding first.")

    # 2. Verify learning need ownership
    learning_need = (
        db.query(LearningNeed)
        .filter(
            LearningNeed.id == payload.learning_need_id,
            LearningNeed.student_profile_id == student_profile.id,
        )
        .first()
    )
    if not learning_need:
        raise ResourceNotFoundException("Learning need not found or does not belong to you.")

    # 3. Retrieve target tutor profile
    tutor_profile = (
        db.query(TutorProfile)
        .options(joinedload(TutorProfile.user), joinedload(TutorProfile.availability))
        .filter(TutorProfile.id == payload.tutor_id)
        .first()
    )
    if not tutor_profile:
        # Fallback query by user_id if passed
        tutor_profile = (
            db.query(TutorProfile)
            .options(joinedload(TutorProfile.user), joinedload(TutorProfile.availability))
            .filter(TutorProfile.user_id == payload.tutor_id)
            .first()
        )
    if not tutor_profile:
        raise ResourceNotFoundException("Tutor profile not found.")

    # 4. Prevent self-booking
    if tutor_profile.user_id == student_user.id:
        raise BadRequestException("Cannot book yourself.")

    # 5. Verify tutor is currently VERIFIED
    if tutor_profile.verification_status != "VERIFIED":
        raise BadRequestException("Cannot book an unverified tutor. Tutor must be fully verified.")

    # 6. Capture tutor's current hourly rate snapshot
    hourly_rate = 0.0
    if tutor_profile.availability:
        rates = [
            float(a.hourly_rate)
            for a in tutor_profile.availability
            if a.hourly_rate is not None and float(a.hourly_rate) > 0
        ]
        if rates:
            hourly_rate = min(rates)

    if hourly_rate <= 0.0:
        hourly_rate = 500.0  # Default platform fallback hourly rate

    total_amount = round(hourly_rate * (payload.duration_minutes / 60.0), 2)

    # 7. Check for duplicate active booking at the same date/time
    existing_duplicate = (
        db.query(Booking)
        .filter(
            Booking.student_id == student_profile.id,
            Booking.tutor_id == tutor_profile.id,
            Booking.scheduled_date == payload.scheduled_date,
            Booking.start_time == payload.start_time,
            Booking.status.in_(["PENDING", "CONFIRMED"]),
        )
        .first()
    )
    if existing_duplicate:
        raise ConflictException(
            "An active booking request for this tutor at the same date and time already exists."
        )

    # 8. Create booking record
    now = datetime.utcnow()
    booking = Booking(
        student_id=student_profile.id,
        tutor_id=tutor_profile.id,
        learning_need_id=learning_need.id,
        scheduled_date=payload.scheduled_date,
        start_time=payload.start_time,
        duration_minutes=payload.duration_minutes,
        hourly_rate=hourly_rate,
        total_amount=total_amount,
        student_message=payload.student_message,
        status="PENDING",
        created_at=now,
        updated_at=now,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    return _format_booking_out(booking)


def list_student_bookings(db: Session, student_user: User) -> List[Dict[str, Any]]:
    student_profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == student_user.id)
        .first()
    )
    if not student_profile:
        return []

    bookings = (
        db.query(Booking)
        .options(
            joinedload(Booking.tutor_profile).joinedload(TutorProfile.user),
            joinedload(Booking.student_profile).joinedload(StudentProfile.user),
            joinedload(Booking.learning_need),
        )
        .filter(Booking.student_id == student_profile.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    return [_format_booking_out(b) for b in bookings]


def list_tutor_booking_requests(db: Session, tutor_user: User) -> List[Dict[str, Any]]:
    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == tutor_user.id)
        .first()
    )
    if not tutor_profile:
        return []

    bookings = (
        db.query(Booking)
        .options(
            joinedload(Booking.tutor_profile).joinedload(TutorProfile.user),
            joinedload(Booking.student_profile).joinedload(StudentProfile.user),
            joinedload(Booking.learning_need),
        )
        .filter(Booking.tutor_id == tutor_profile.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    return [_format_booking_out(b) for b in bookings]


def decide_booking_request(
    db: Session,
    tutor_user: User,
    booking_id: str,
    decision: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == tutor_user.id)
        .first()
    )
    if not tutor_profile:
        raise BadRequestException("Tutor profile not found.")

    booking = (
        db.query(Booking)
        .options(
            joinedload(Booking.tutor_profile).joinedload(TutorProfile.user),
            joinedload(Booking.student_profile).joinedload(StudentProfile.user),
            joinedload(Booking.learning_need),
        )
        .filter(Booking.id == booking_id)
        .first()
    )
    if not booking:
        raise ResourceNotFoundException("Booking request not found.")

    if booking.tutor_id != tutor_profile.id:
        raise RoleForbiddenException("You are not authorized to decide this booking request.")

    if booking.status != "PENDING":
        raise BadRequestException(
            f"Cannot update booking in '{booking.status}' status. Only PENDING requests can be decided."
        )

    decision_upper = decision.upper().strip()
    if decision_upper == "ACCEPTED":
        booking.status = "CONFIRMED"
        # Automatic session creation on booking confirmation
        from backend.app.models.session import Session as SessionModel
        existing_session = (
            db.query(SessionModel)
            .filter(SessionModel.booking_id == booking.id)
            .first()
        )
        if not existing_session:
            now = datetime.utcnow()
            new_session = SessionModel(
                booking_id=booking.id,
                student_id=booking.student_id,
                tutor_id=booking.tutor_id,
                learning_need_id=booking.learning_need_id,
                scheduled_date=booking.scheduled_date,
                start_time=booking.start_time,
                duration_minutes=booking.duration_minutes,
                status="SCHEDULED",
                created_at=now,
                updated_at=now,
            )
            db.add(new_session)
    elif decision_upper == "REJECTED":
        booking.status = "REJECTED"
    else:
        raise BadRequestException("Decision must be either ACCEPTED or REJECTED.")

    booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)

    return _format_booking_out(booking)


def cancel_booking(
    db: Session,
    user: User,
    booking_id: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    booking = (
        db.query(Booking)
        .options(
            joinedload(Booking.tutor_profile).joinedload(TutorProfile.user),
            joinedload(Booking.student_profile).joinedload(StudentProfile.user),
            joinedload(Booking.learning_need),
        )
        .filter(Booking.id == booking_id)
        .first()
    )
    if not booking:
        raise ResourceNotFoundException("Booking not found.")

    # Check authority
    is_owner = False
    if user.role == "STUDENT":
        student_profile = (
            db.query(StudentProfile)
            .filter(StudentProfile.user_id == user.id)
            .first()
        )
        if student_profile and booking.student_id == student_profile.id:
            is_owner = True
    elif user.role == "TUTOR":
        tutor_profile = (
            db.query(TutorProfile)
            .filter(TutorProfile.user_id == user.id)
            .first()
        )
        if tutor_profile and booking.tutor_id == tutor_profile.id:
            is_owner = True

    if not is_owner:
        raise RoleForbiddenException("You are not authorized to cancel this booking.")

    if booking.status not in ("PENDING", "CONFIRMED"):
        raise BadRequestException(f"Cannot cancel booking with status '{booking.status}'.")

    now = datetime.utcnow()
    booking.status = "CANCELLED"
    booking.updated_at = now

    # Also cancel associated SCHEDULED session if one was created
    from backend.app.models.session import Session as SessionModel
    associated_session = (
        db.query(SessionModel)
        .filter(SessionModel.booking_id == booking.id)
        .first()
    )
    if associated_session and associated_session.status == "SCHEDULED":
        associated_session.status = "CANCELLED"
        associated_session.cancellation_reason = reason or "Booking cancelled"
        associated_session.updated_at = now

    db.commit()
    db.refresh(booking)

    return _format_booking_out(booking)
