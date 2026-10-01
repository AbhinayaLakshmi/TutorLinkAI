from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.services.auth import get_current_user, require_role
from backend.app.schemas.booking import (
    BookingCreate,
    BookingDecision,
    BookingCancel,
    BookingOut,
)
from backend.app.modules.booking import service as booking_service

router = APIRouter(prefix="/api/booking", tags=["booking"])


@router.post(
    "",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("STUDENT"))],
)
def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new PENDING booking request from an authenticated student
    to a verified tutor for a specific LearningNeed.
    """
    try:
        return booking_service.create_booking(db, current_user, payload)
    except Exception as e:
        if hasattr(e, "status_code"):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/student",
    response_model=List[BookingOut],
    dependencies=[Depends(require_role("STUDENT"))],
)
def get_student_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all booking requests and confirmed sessions created by the authenticated student.
    """
    try:
        return booking_service.list_student_bookings(db, current_user)
    except Exception as e:
        if hasattr(e, "status_code"):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/tutor/requests",
    response_model=List[BookingOut],
    dependencies=[Depends(require_role("TUTOR"))],
)
def get_tutor_booking_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns all incoming booking requests directed to the authenticated tutor.
    """
    try:
        return booking_service.list_tutor_booking_requests(db, current_user)
    except Exception as e:
        if hasattr(e, "status_code"):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{booking_id}/decision",
    response_model=BookingOut,
    dependencies=[Depends(require_role("TUTOR"))],
)
def decide_booking_request(
    booking_id: str,
    payload: BookingDecision,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tutor endpoint to ACCEPT (becomes CONFIRMED) or REJECT a PENDING booking request.
    """
    try:
        return booking_service.decide_booking_request(
            db, current_user, booking_id, payload.decision, payload.reason
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingOut,
)
def cancel_booking(
    booking_id: str,
    payload: BookingCancel = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Allows a student or tutor to cancel an active (PENDING or CONFIRMED) booking.
    """
    try:
        reason = payload.reason if payload else None
        return booking_service.cancel_booking(db, current_user, booking_id, reason)
    except Exception as e:
        if hasattr(e, "status_code"):
            raise e
        raise HTTPException(status_code=400, detail=str(e))
