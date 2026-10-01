from datetime import datetime
from typing import List, Optional, Dict
from fastapi import HTTPException, status
from sqlalchemy.orm import Session as DBSession

from backend.app.models.review import Review
from backend.app.models.session import Session as TutoringSession
from backend.app.models.student import StudentProfile
from backend.app.models.tutor import TutorProfile
from backend.app.models.user import User
from backend.app.schemas.review import ReviewCreate, ReviewOut, TutorReviewSummary


def _build_review_out(review: Review, db: DBSession) -> ReviewOut:
    student_name = None
    tutor_name = None

    if review.student_id:
        student_profile = db.query(StudentProfile).filter(StudentProfile.id == review.student_id).first()
        if student_profile and student_profile.user_id:
            user = db.query(User).filter(User.id == student_profile.user_id).first()
            if user:
                student_name = user.full_name

    if review.tutor_id:
        tutor_profile = db.query(TutorProfile).filter(TutorProfile.id == review.tutor_id).first()
        if tutor_profile and tutor_profile.user_id:
            user = db.query(User).filter(User.id == tutor_profile.user_id).first()
            if user:
                tutor_name = user.full_name

    return ReviewOut(
        id=review.id,
        session_id=review.session_id,
        student_id=review.student_id,
        tutor_id=review.tutor_id,
        rating=review.rating,
        review_text=review.review_text,
        student_name=student_name,
        tutor_name=tutor_name,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def create_review(
    db: DBSession,
    session_id: str,
    student_profile_id: str,
    payload: ReviewCreate,
) -> ReviewOut:
    """
    Create a review for a completed session by the assigned student.
    Strictly validates session ownership, completion state, and single-review rule.
    """
    session = db.query(TutoringSession).filter(TutoringSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutoring session not found."
        )

    # Validate that current student is the participant
    if session.student_id != student_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only review your own completed sessions."
        )

    # Validate session status is COMPLETED
    if session.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review a session with status '{session.status}'. Only COMPLETED sessions can be reviewed."
        )

    # Validate single review per session
    existing_review = db.query(Review).filter(Review.session_id == session.id).first()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A review has already been submitted for this session."
        )

    # Validate rating
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be an integer between 1 and 5."
        )

    # Handle optional review text
    cleaned_text = payload.review_text.strip() if payload.review_text else None
    if cleaned_text == "":
        cleaned_text = None

    now = datetime.utcnow()
    review = Review(
        session_id=session.id,
        student_id=session.student_id,
        tutor_id=session.tutor_id,
        rating=payload.rating,
        review_text=cleaned_text,
        created_at=now,
        updated_at=now,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return _build_review_out(review, db)


def get_tutor_reviews(db: DBSession, tutor_profile_id: str) -> List[ReviewOut]:
    """
    Retrieve all public reviews submitted for a specific tutor.
    """
    reviews = (
        db.query(Review)
        .filter(Review.tutor_id == tutor_profile_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    return [_build_review_out(r, db) for r in reviews]


def get_tutor_review_summary(db: DBSession, tutor_profile_id: str) -> TutorReviewSummary:
    """
    Compute aggregate average rating, review count, and rating distribution for a tutor.
    """
    reviews = db.query(Review).filter(Review.tutor_id == tutor_profile_id).all()
    total_reviews = len(reviews)
    distribution: Dict[str, int] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

    if total_reviews == 0:
        return TutorReviewSummary(
            average_rating=0.0,
            total_reviews=0,
            rating_distribution=distribution
        )

    total_score = 0
    for r in reviews:
        total_score += r.rating
        key = str(r.rating)
        if key in distribution:
            distribution[key] += 1

    average_rating = round(total_score / total_reviews, 1)

    return TutorReviewSummary(
        average_rating=average_rating,
        total_reviews=total_reviews,
        rating_distribution=distribution
    )


def get_session_review(
    db: DBSession,
    session_id: str,
    user_id: str,
    user_role: str,
) -> ReviewOut:
    """
    Retrieve the review associated with a session.
    Enforces authorization to ensure only participants or authorized viewers access it.
    """
    session = db.query(TutoringSession).filter(TutoringSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    # Authorization check
    role_upper = (user_role or "").upper()
    if role_upper == "STUDENT":
        student_profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
        if not student_profile or session.student_id != student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session review."
            )
    elif role_upper == "TUTOR":
        tutor_profile = db.query(TutorProfile).filter(TutorProfile.user_id == user_id).first()
        if not tutor_profile or session.tutor_id != tutor_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session review."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session review."
        )

    review = db.query(Review).filter(Review.session_id == session_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No review has been submitted for this session."
        )

    return _build_review_out(review, db)
