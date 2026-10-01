from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session as DBSession

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.student import StudentProfile
from backend.app.models.tutor import TutorProfile
from backend.app.services.auth import require_role, get_current_user
from backend.app.schemas.review import ReviewCreate, ReviewOut, TutorReviewSummary
from backend.app.modules.review import service as review_service

review_router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


@review_router.post("/{session_id}", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_session_review(
    session_id: str,
    payload: ReviewCreate,
    current_user: User = Depends(require_role("student")),
    db: DBSession = Depends(get_db)
):
    """
    Submit a review and rating for a COMPLETED tutoring session.
    Allowed only for the student assigned to the session.
    """
    student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found."
        )

    return review_service.create_review(
        db=db,
        session_id=session_id,
        student_profile_id=student_profile.id,
        payload=payload
    )


@review_router.get("/tutor/{tutor_id}", response_model=List[ReviewOut])
def get_reviews_for_tutor(
    tutor_id: str,
    db: DBSession = Depends(get_db)
):
    """
    Retrieve all public reviews for a specific tutor profile.
    """
    return review_service.get_tutor_reviews(db=db, tutor_profile_id=tutor_id)


@review_router.get("/tutor/{tutor_id}/summary", response_model=TutorReviewSummary)
def get_tutor_summary(
    tutor_id: str,
    db: DBSession = Depends(get_db)
):
    """
    Get aggregate review metrics (average rating, review count, rating distribution) for a tutor.
    """
    return review_service.get_tutor_review_summary(db=db, tutor_profile_id=tutor_id)


@review_router.get("/session/{session_id}", response_model=ReviewOut)
def get_review_for_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """
    Retrieve the review associated with a session if the caller is the assigned student or tutor.
    """
    return review_service.get_session_review(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        user_role=current_user.role
    )
