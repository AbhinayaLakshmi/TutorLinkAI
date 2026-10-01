import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from backend.app.core.exceptions import (
    BadRequestException,
    ResourceNotFoundException,
    RoleForbiddenException,
)
from backend.app.models.user import User
from backend.app.models.student import StudentProfile
from backend.app.models.tutor import TutorProfile
from backend.app.models.booking import Booking
from backend.app.models.session import Session as SessionModel
from backend.app.schemas.session import SessionComplete, SessionCancel

logger = logging.getLogger("session_service")


def _format_session_out(session: SessionModel) -> Dict[str, Any]:
    """Helper to assemble rich display metadata for SessionOut responses."""
    tutor_profile = session.tutor_profile
    tutor_user = tutor_profile.user if tutor_profile else None

    student_profile = session.student_profile
    student_user = student_profile.user if student_profile else None

    learning_need = session.learning_need

    return {
        "id": session.id,
        "booking_id": session.booking_id,
        "student_id": session.student_id,
        "tutor_id": session.tutor_id,
        "learning_need_id": session.learning_need_id,
        "learning_need_title": learning_need.title if learning_need else None,
        "scheduled_date": session.scheduled_date,
        "start_time": session.start_time,
        "duration_minutes": session.duration_minutes,
        "status": session.status,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "actual_duration_minutes": session.actual_duration_minutes,
        "completion_note": session.completion_note,
        "cancellation_reason": session.cancellation_reason,
        "tutor_name": tutor_user.full_name if tutor_user else "Tutor",
        "tutor_email": tutor_user.email if tutor_user else None,
        "tutor_location": tutor_profile.location if tutor_profile else None,
        "tutor_profile_picture_path": tutor_profile.profile_picture_path if tutor_profile else None,
        "student_name": student_user.full_name if student_user else "Student",
        "student_email": student_user.email if student_user else None,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


def create_session_from_booking(db: Session, booking: Booking) -> SessionModel:
    """Internal service helper to create a SCHEDULED session from a CONFIRMED booking."""
    if booking.status != "CONFIRMED":
        raise BadRequestException("Cannot create a session for an unconfirmed booking.")

    existing_session = (
        db.query(SessionModel)
        .filter(SessionModel.booking_id == booking.id)
        .first()
    )
    if existing_session:
        return existing_session

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
    db.commit()
    db.refresh(new_session)
    return new_session


def list_student_sessions(db: Session, student_user: User) -> List[Dict[str, Any]]:
    student_profile = (
        db.query(StudentProfile)
        .filter(StudentProfile.user_id == student_user.id)
        .first()
    )
    if not student_profile:
        return []

    sessions = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.tutor_profile).joinedload(TutorProfile.user),
            joinedload(SessionModel.student_profile).joinedload(StudentProfile.user),
            joinedload(SessionModel.learning_need),
            joinedload(SessionModel.booking),
        )
        .filter(SessionModel.student_id == student_profile.id)
        .order_by(SessionModel.created_at.desc())
        .all()
    )

    return [_format_session_out(s) for s in sessions]


def list_tutor_sessions(db: Session, tutor_user: User) -> List[Dict[str, Any]]:
    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == tutor_user.id)
        .first()
    )
    if not tutor_profile:
        return []

    sessions = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.tutor_profile).joinedload(TutorProfile.user),
            joinedload(SessionModel.student_profile).joinedload(StudentProfile.user),
            joinedload(SessionModel.learning_need),
            joinedload(SessionModel.booking),
        )
        .filter(SessionModel.tutor_id == tutor_profile.id)
        .order_by(SessionModel.created_at.desc())
        .all()
    )

    return [_format_session_out(s) for s in sessions]


def get_session_by_id(db: Session, user: User, session_id: str) -> Dict[str, Any]:
    session = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.tutor_profile).joinedload(TutorProfile.user),
            joinedload(SessionModel.student_profile).joinedload(StudentProfile.user),
            joinedload(SessionModel.learning_need),
            joinedload(SessionModel.booking),
        )
        .filter(SessionModel.id == session_id)
        .first()
    )
    if not session:
        raise ResourceNotFoundException("Session not found.")

    is_authorized = False
    if user.role == "STUDENT":
        if session.student_profile and session.student_profile.user_id == user.id:
            is_authorized = True
    elif user.role == "TUTOR":
        if session.tutor_profile and session.tutor_profile.user_id == user.id:
            is_authorized = True

    if not is_authorized:
        raise RoleForbiddenException("You are not authorized to access this session.")

    return _format_session_out(session)


def start_session(db: Session, tutor_user: User, session_id: str) -> Dict[str, Any]:
    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == tutor_user.id)
        .first()
    )
    if not tutor_profile:
        raise BadRequestException("Tutor profile not found.")

    session = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.tutor_profile).joinedload(TutorProfile.user),
            joinedload(SessionModel.student_profile).joinedload(StudentProfile.user),
            joinedload(SessionModel.learning_need),
            joinedload(SessionModel.booking),
        )
        .filter(SessionModel.id == session_id)
        .first()
    )
    if not session:
        raise ResourceNotFoundException("Session not found.")

    if session.tutor_id != tutor_profile.id:
        raise RoleForbiddenException("You are not authorized to start this session.")

    if session.status != "SCHEDULED":
        raise BadRequestException(
            f"Cannot start session in '{session.status}' status. Only SCHEDULED sessions can be started."
        )

    now = datetime.utcnow()
    session.status = "IN_PROGRESS"
    session.started_at = now
    session.updated_at = now
    db.commit()
    db.refresh(session)

    return _format_session_out(session)


def complete_session(
    db: Session,
    tutor_user: User,
    session_id: str,
    payload: SessionComplete,
) -> Dict[str, Any]:
    tutor_profile = (
        db.query(TutorProfile)
        .filter(TutorProfile.user_id == tutor_user.id)
        .first()
    )
    if not tutor_profile:
        raise BadRequestException("Tutor profile not found.")

    session = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.tutor_profile).joinedload(TutorProfile.user),
            joinedload(SessionModel.student_profile).joinedload(StudentProfile.user),
            joinedload(SessionModel.learning_need),
            joinedload(SessionModel.booking),
        )
        .filter(SessionModel.id == session_id)
        .first()
    )
    if not session:
        raise ResourceNotFoundException("Session not found.")

    if session.tutor_id != tutor_profile.id:
        raise RoleForbiddenException("You are not authorized to complete this session.")

    if session.status != "IN_PROGRESS":
        raise BadRequestException(
            f"Cannot complete session in '{session.status}' status. Only IN_PROGRESS sessions can be completed."
        )

    now = datetime.utcnow()
    session.status = "COMPLETED"
    session.ended_at = now
    if session.started_at:
        seconds_elapsed = (session.ended_at - session.started_at).total_seconds()
        session.actual_duration_minutes = max(1, round(seconds_elapsed / 60.0))
    else:
        session.actual_duration_minutes = session.duration_minutes

    if payload.completion_note is not None:
        session.completion_note = payload.completion_note

    session.updated_at = now
    db.commit()
    db.refresh(session)

    return _format_session_out(session)


def cancel_session(
    db: Session,
    user: User,
    session_id: str,
    payload: SessionCancel,
) -> Dict[str, Any]:
    session = (
        db.query(SessionModel)
        .options(
            joinedload(SessionModel.tutor_profile).joinedload(TutorProfile.user),
            joinedload(SessionModel.student_profile).joinedload(StudentProfile.user),
            joinedload(SessionModel.learning_need),
            joinedload(SessionModel.booking),
        )
        .filter(SessionModel.id == session_id)
        .first()
    )
    if not session:
        raise ResourceNotFoundException("Session not found.")

    # Check participant authorization
    is_authorized = False
    if user.role == "STUDENT":
        if session.student_profile and session.student_profile.user_id == user.id:
            is_authorized = True
    elif user.role == "TUTOR":
        if session.tutor_profile and session.tutor_profile.user_id == user.id:
            is_authorized = True

    if not is_authorized:
        raise RoleForbiddenException("You are not authorized to cancel this session.")

    if session.status != "SCHEDULED":
        raise BadRequestException(
            f"Cannot cancel session with status '{session.status}'. Only SCHEDULED sessions can be cancelled."
        )

    now = datetime.utcnow()
    session.status = "CANCELLED"
    if payload.reason is not None:
        session.cancellation_reason = payload.reason

    session.updated_at = now
    db.commit()
    db.refresh(session)

    return _format_session_out(session)
