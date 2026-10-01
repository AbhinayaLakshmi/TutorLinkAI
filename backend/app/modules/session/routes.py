from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.services.auth import get_current_user, require_role
from backend.app.models.user import User
from backend.app.schemas.session import (
    SessionOut,
    SessionStart,
    SessionComplete,
    SessionCancel,
)
from backend.app.modules.session import service as session_service

router = APIRouter(prefix="/api/session", tags=["Sessions"])


@router.get("/student", response_model=List[SessionOut], status_code=status.HTTP_200_OK)
def get_student_sessions(
    current_user: User = Depends(require_role(["STUDENT"])),
    db: Session = Depends(get_db),
):
    """Retrieve all sessions for the authenticated student."""
    return session_service.list_student_sessions(db, current_user)


@router.get("/tutor", response_model=List[SessionOut], status_code=status.HTTP_200_OK)
def get_tutor_sessions(
    current_user: User = Depends(require_role(["TUTOR"])),
    db: Session = Depends(get_db),
):
    """Retrieve all sessions for the authenticated tutor."""
    return session_service.list_tutor_sessions(db, current_user)


@router.get("/{session_id}", response_model=SessionOut, status_code=status.HTTP_200_OK)
def get_session_details(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details of a single session (authorized student or tutor only)."""
    return session_service.get_session_by_id(db, current_user, session_id)


@router.post("/{session_id}/start", response_model=SessionOut, status_code=status.HTTP_200_OK)
def start_session(
    session_id: str,
    current_user: User = Depends(require_role(["TUTOR"])),
    db: Session = Depends(get_db),
):
    """Tutor starts a SCHEDULED session, transitioning it to IN_PROGRESS."""
    return session_service.start_session(db, current_user, session_id)


@router.post("/{session_id}/complete", response_model=SessionOut, status_code=status.HTTP_200_OK)
def complete_session(
    session_id: str,
    payload: SessionComplete,
    current_user: User = Depends(require_role(["TUTOR"])),
    db: Session = Depends(get_db),
):
    """Tutor completes an IN_PROGRESS session, calculating actual duration."""
    return session_service.complete_session(db, current_user, session_id, payload)


@router.post("/{session_id}/cancel", response_model=SessionOut, status_code=status.HTTP_200_OK)
def cancel_session(
    session_id: str,
    payload: SessionCancel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Student or Tutor cancels a SCHEDULED session."""
    return session_service.cancel_session(db, current_user, session_id, payload)
