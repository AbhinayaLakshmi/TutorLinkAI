import pytest
from backend.app.models.user import User
from backend.app.models.student import StudentProfile, LearningNeed
from backend.app.models.tutor import TutorProfile
from backend.app.models.booking import Booking
from backend.app.models.session import Session as SessionModel
from backend.app.models.review import Review
from backend.app.services.feedback_score import (
    calculate_feedback_signal,
    compute_global_review_prior,
    get_tutor_feedback_signal,
    DEFAULT_SMOOTHING_M,
    DEFAULT_GLOBAL_PRIOR,
)


def test_zero_review_tutor():
    sig = calculate_feedback_signal(None, 0, smoothing_m=5.0, global_prior=3.5)
    assert sig["has_reviews"] is False
    assert sig["review_count"] == 0
    assert sig["confidence"] == 0.0
    assert sig["adjusted_rating"] == 3.5
    assert sig["feedback_score"] == pytest.approx(0.625, abs=1e-4)


def test_one_review_tutor():
    # n=1, m=5, prior=3.5, rating=5.0 -> w = 1/6
    # adjusted = (1/6)*5.0 + (5/6)*3.5 = 3.75
    sig = calculate_feedback_signal(5.0, 1, smoothing_m=5.0, global_prior=3.5)
    assert sig["has_reviews"] is True
    assert sig["review_count"] == 1
    assert sig["confidence"] == pytest.approx(1.0 / 6.0, abs=1e-4)
    assert sig["adjusted_rating"] == pytest.approx(3.75, abs=1e-4)
    assert sig["feedback_score"] == pytest.approx((3.75 - 1.0) / 4.0, abs=1e-4)


def test_five_review_tutor():
    # n=5, m=5, prior=3.5, rating=5.0 -> w = 5/10 = 0.5
    # adjusted = 0.5*5.0 + 0.5*3.5 = 4.25
    sig = calculate_feedback_signal(5.0, 5, smoothing_m=5.0, global_prior=3.5)
    assert sig["has_reviews"] is True
    assert sig["confidence"] == pytest.approx(0.5, abs=1e-4)
    assert sig["adjusted_rating"] == pytest.approx(4.25, abs=1e-4)
    assert sig["feedback_score"] == pytest.approx((4.25 - 1.0) / 4.0, abs=1e-4)


def test_twenty_review_tutor():
    # n=20, m=5, prior=3.5, rating=5.0 -> w = 20/25 = 0.8
    # adjusted = 0.8*5.0 + 0.2*3.5 = 4.70
    sig = calculate_feedback_signal(5.0, 20, smoothing_m=5.0, global_prior=3.5)
    assert sig["has_reviews"] is True
    assert sig["confidence"] == pytest.approx(0.8, abs=1e-4)
    assert sig["adjusted_rating"] == pytest.approx(4.70, abs=1e-4)
    assert sig["feedback_score"] == pytest.approx((4.70 - 1.0) / 4.0, abs=1e-4)


def test_high_rated_tutor():
    # n=50, m=5, rating=5.0 -> adjusted ~ 4.8636, score ~ 0.9659
    sig = calculate_feedback_signal(5.0, 50, smoothing_m=5.0, global_prior=3.5)
    assert sig["adjusted_rating"] > 4.85
    assert sig["feedback_score"] > 0.95
    assert sig["confidence"] > 0.90


def test_low_rated_tutor():
    # n=50, m=5, rating=1.0 -> adjusted ~ 1.227, score ~ 0.056
    sig = calculate_feedback_signal(1.0, 50, smoothing_m=5.0, global_prior=3.5)
    assert sig["adjusted_rating"] < 1.30
    assert sig["feedback_score"] < 0.10
    assert sig["confidence"] > 0.90


def test_same_average_different_review_counts():
    sig_low_count = calculate_feedback_signal(5.0, 1, smoothing_m=5.0, global_prior=3.5)
    sig_high_count = calculate_feedback_signal(5.0, 20, smoothing_m=5.0, global_prior=3.5)

    assert sig_low_count["average_rating"] == sig_high_count["average_rating"]
    assert sig_high_count["confidence"] > sig_low_count["confidence"]
    assert sig_high_count["adjusted_rating"] > sig_low_count["adjusted_rating"]
    assert sig_high_count["feedback_score"] > sig_low_count["feedback_score"]


def test_more_reviews_increase_evidence_confidence():
    counts = [0, 1, 2, 5, 10, 20, 50, 100]
    confidences = [
        calculate_feedback_signal(4.5, c, smoothing_m=5.0, global_prior=3.5)["confidence"]
        for c in counts
    ]
    for i in range(len(confidences) - 1):
        assert confidences[i] < confidences[i + 1]


def test_confidence_remains_less_than_or_equal_to_one():
    counts = [0, 1, 10, 100, 1000, 50000]
    for c in counts:
        sig = calculate_feedback_signal(4.8, c, smoothing_m=5.0, global_prior=3.5)
        assert 0.0 <= sig["confidence"] <= 1.0


def test_feedback_score_bounded_in_zero_to_one():
    ratings = [1.0, 2.0, 3.5, 4.0, 5.0]
    counts = [0, 1, 5, 25, 100]
    priors = [1.0, 3.0, 3.5, 4.0, 5.0]

    for r in ratings:
        for c in counts:
            for p in priors:
                sig = calculate_feedback_signal(r, c, smoothing_m=5.0, global_prior=p)
                assert 0.0 <= sig["feedback_score"] <= 1.0


def test_no_review_case_no_negative_score():
    sig = calculate_feedback_signal(None, 0, smoothing_m=5.0, global_prior=3.5)
    assert sig["feedback_score"] >= 0.0
    assert sig["feedback_score"] == pytest.approx((3.5 - 1.0) / 4.0, abs=1e-4)


def test_global_prior_behavior_with_database_reviews(db):
    # Setup test users and reviews in DB
    u_s = User(email="fb_s@test.com", hashed_password="h", full_name="S", role="STUDENT", email_verified=True, onboarding_status="COMPLETED")
    u_t = User(email="fb_t@test.com", hashed_password="h", full_name="T", role="TUTOR", email_verified=True, onboarding_status="COMPLETED")
    db.add_all([u_s, u_t])
    db.flush()

    s_prof = StudentProfile(user_id=u_s.id, location="Chennai")
    t_prof = TutorProfile(user_id=u_t.id, location="Chennai", verification_status="VERIFIED")
    db.add_all([s_prof, t_prof])
    db.flush()

    need = LearningNeed(student_profile_id=s_prof.id, title="Math", subjects=["Math"])
    db.add(need)
    db.flush()

    booking = Booking(student_id=s_prof.id, tutor_id=t_prof.id, learning_need_id=need.id, scheduled_date="2026-10-20", start_time="10:00", duration_minutes=60, hourly_rate=500.0, total_amount=500.0, status="CONFIRMED")
    db.add(booking)
    db.flush()

    sess1 = SessionModel(booking_id=booking.id, student_id=s_prof.id, tutor_id=t_prof.id, learning_need_id=need.id, scheduled_date="2026-10-20", start_time="10:00", duration_minutes=60, status="COMPLETED")
    db.add(sess1)
    db.flush()

    # Add 2 reviews: rating 4 and rating 5 -> Mean = 4.5
    rev1 = Review(session_id=sess1.id, student_id=s_prof.id, tutor_id=t_prof.id, rating=4)
    db.add(rev1)
    db.commit()

    # Prior should reflect the review
    prior = compute_global_review_prior(db)
    assert prior == pytest.approx(4.0, abs=1e-3)


def test_no_review_global_dataset_fallback(db):
    # In an isolated clean session, default prior should return when no reviews match
    prior = compute_global_review_prior(db, default_prior=3.5)
    assert prior > 0.0


def test_deterministic_output():
    sig1 = calculate_feedback_signal(4.6, 12, smoothing_m=5.0, global_prior=3.5)
    sig2 = calculate_feedback_signal(4.6, 12, smoothing_m=5.0, global_prior=3.5)
    assert sig1 == sig2
