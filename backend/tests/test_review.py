import uuid
from datetime import datetime, timedelta
import pytest
from fastapi import status

from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.models.student import StudentProfile, LearningNeed
from backend.app.models.tutor import TutorProfile, Availability
from backend.app.models.booking import Booking
from backend.app.models.session import Session as SessionModel
from backend.app.models.review import Review


def _create_test_student(db, email="student_rev@example.com", name="Review Student"):
    user = User(
        email=email,
        hashed_password="hashedpassword123",
        full_name=name,
        phone_number="9876543220",
        role="STUDENT",
        email_verified=True,
        onboarding_status="COMPLETED",
    )
    db.add(user)
    db.flush()

    profile = StudentProfile(
        user_id=user.id,
        student_type="UNIVERSITY",
        university="Anna University",
        course="Computer Science",
        year_of_study=3,
        location="Chennai",
        preferred_learning_mode="Online",
        preferred_tutor_languages=["English"],
    )
    db.add(profile)
    db.flush()

    need = LearningNeed(
        student_profile_id=profile.id,
        title="Distributed Systems & Consensus",
        subjects=["Computer Science"],
        topics=["Raft", "Paxos"],
        learning_goals="Understand consensus protocols",
        budget_min=500.0,
        budget_max=1000.0,
        is_active=True,
    )
    db.add(need)
    db.commit()
    db.refresh(user)
    db.refresh(profile)
    db.refresh(need)

    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return user, profile, need, headers


def _create_test_tutor(
    db,
    email="tutor_rev@example.com",
    name="Verified Review Tutor",
    hourly_rate=800.0,
):
    user = User(
        email=email,
        hashed_password="hashedpassword123",
        full_name=name,
        phone_number="9876543221",
        role="TUTOR",
        email_verified=True,
        onboarding_status="COMPLETED",
    )
    db.add(user)
    db.flush()

    profile = TutorProfile(
        user_id=user.id,
        location="Chennai",
        preferred_teaching_mode="Online",
        verification_status="VERIFIED",
        languages_spoken=["English"],
    )
    db.add(profile)
    db.flush()

    availability = Availability(
        tutor_profile_id=profile.id,
        day_of_week="Wednesday",
        time_ranges=[{"start": "09:00", "end": "18:00"}],
        preferred_session_duration=60,
        hourly_rate=hourly_rate,
    )
    db.add(availability)
    db.commit()
    db.refresh(user)
    db.refresh(profile)

    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return user, profile, headers


def _create_completed_session(db, student_profile, tutor_profile, need):
    booking = Booking(
        student_id=student_profile.id,
        tutor_id=tutor_profile.id,
        learning_need_id=need.id,
        scheduled_date="2026-10-15",
        start_time="14:00",
        duration_minutes=60,
        hourly_rate=800.0,
        total_amount=800.0,
        status="CONFIRMED",
    )
    db.add(booking)
    db.flush()

    now = datetime.utcnow()
    session = SessionModel(
        booking_id=booking.id,
        student_id=student_profile.id,
        tutor_id=tutor_profile.id,
        learning_need_id=need.id,
        scheduled_date="2026-10-15",
        start_time="14:00",
        duration_minutes=60,
        status="COMPLETED",
        started_at=now - timedelta(minutes=60),
        ended_at=now,
        actual_duration_minutes=60,
        completion_note="Covered consensus and completed session.",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def test_create_review_for_completed_session(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_c1@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_c1@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload = {
        "rating": 5,
        "review_text": "Outstanding session! Clear explanation of Paxos."
    }

    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["session_id"] == session.id
    assert data["student_id"] == student_profile.id
    assert data["tutor_id"] == tutor_profile.id
    assert data["rating"] == 5
    assert data["review_text"] == "Outstanding session! Clear explanation of Paxos."


def test_reject_review_for_scheduled_session(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_sch@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_sch@test.com")
    
    session = _create_completed_session(db, student_profile, tutor_profile, need)
    session.status = "SCHEDULED"
    db.commit()

    payload = {"rating": 5, "review_text": "Too early"}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "SCHEDULED" in res.json()["detail"]


def test_reject_review_for_in_progress_session(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_inp@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_inp@test.com")
    
    session = _create_completed_session(db, student_profile, tutor_profile, need)
    session.status = "IN_PROGRESS"
    db.commit()

    payload = {"rating": 5, "review_text": "Still ongoing"}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "IN_PROGRESS" in res.json()["detail"]


def test_reject_review_for_cancelled_session(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_can@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_can@test.com")
    
    session = _create_completed_session(db, student_profile, tutor_profile, need)
    session.status = "CANCELLED"
    db.commit()

    payload = {"rating": 1, "review_text": "Was cancelled"}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "CANCELLED" in res.json()["detail"]


def test_reject_second_review_for_same_session(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_dup@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_dup@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload1 = {"rating": 4, "review_text": "First review"}
    res1 = client.post(f"/api/reviews/{session.id}", json=payload1, headers=student_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    payload2 = {"rating": 5, "review_text": "Second attempt"}
    res2 = client.post(f"/api/reviews/{session.id}", json=payload2, headers=student_headers)
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already" in res2.json()["detail"].lower()


def test_reject_student_reviewing_another_students_session(client, db):
    _, student_profile_a, need_a, _ = _create_test_student(db, "s_a@test.com")
    _, student_profile_b, _, student_headers_b = _create_test_student(db, "s_b@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_cross@test.com")

    session = _create_completed_session(db, student_profile_a, tutor_profile, need_a)

    # Student B attempts to review Student A's session
    payload = {"rating": 5, "review_text": "Intruder review"}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers_b)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_reject_unauthenticated_review_creation(client, db):
    _, student_profile, need, _ = _create_test_student(db, "s_unauth@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_unauth@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload = {"rating": 5, "review_text": "No auth"}
    res = client.post(f"/api/reviews/{session.id}", json=payload)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_reject_tutor_attempting_to_create_review(client, db):
    _, student_profile, need, _ = _create_test_student(db, "s_tutrev@test.com")
    _, tutor_profile, tutor_headers = _create_test_tutor(db, "t_tutrev@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload = {"rating": 5, "review_text": "Tutor self review"}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=tutor_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_reject_rating_below_1(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_low@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_low@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload = {"rating": 0, "review_text": "Invalid low rating"}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_reject_rating_above_5(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_high@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_high@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload = {"rating": 6, "review_text": "Invalid high rating"}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_allow_rating_1(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_r1@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_r1@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload = {"rating": 1, "review_text": "Disappointing session"}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["rating"] == 1


def test_allow_rating_5(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_r5@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_r5@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload = {"rating": 5, "review_text": "Excellent explanation!"}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["rating"] == 5


def test_optional_review_text(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_opt@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_opt@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload = {"rating": 4}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["rating"] == 4
    assert res.json()["review_text"] is None


def test_empty_whitespace_review_handling(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_space@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_space@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    payload = {"rating": 4, "review_text": "   "}
    res = client.post(f"/api/reviews/{session.id}", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["review_text"] is None


def test_retrieve_tutor_reviews(client, db):
    _, student_profile_1, need_1, headers_1 = _create_test_student(db, "s_t1@test.com", "Student One")
    _, student_profile_2, need_2, headers_2 = _create_test_student(db, "s_t2@test.com", "Student Two")
    _, tutor_profile, _ = _create_test_tutor(db, "t_list@test.com")

    session_1 = _create_completed_session(db, student_profile_1, tutor_profile, need_1)
    session_2 = _create_completed_session(db, student_profile_2, tutor_profile, need_2)

    client.post(f"/api/reviews/{session_1.id}", json={"rating": 5, "review_text": "Super!"}, headers=headers_1)
    client.post(f"/api/reviews/{session_2.id}", json={"rating": 4, "review_text": "Great!"}, headers=headers_2)

    res = client.get(f"/api/reviews/tutor/{tutor_profile.id}")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert len(data) == 2
    ratings = [d["rating"] for d in data]
    assert 5 in ratings and 4 in ratings


def test_calculate_tutor_average_rating(client, db):
    _, student_profile_1, need_1, headers_1 = _create_test_student(db, "s_avg1@test.com")
    _, student_profile_2, need_2, headers_2 = _create_test_student(db, "s_avg2@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_avg@test.com")

    session_1 = _create_completed_session(db, student_profile_1, tutor_profile, need_1)
    session_2 = _create_completed_session(db, student_profile_2, tutor_profile, need_2)

    client.post(f"/api/reviews/{session_1.id}", json={"rating": 4}, headers=headers_1)
    client.post(f"/api/reviews/{session_2.id}", json={"rating": 5}, headers=headers_2)

    res = client.get(f"/api/reviews/tutor/{tutor_profile.id}/summary")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["total_reviews"] == 2
    assert data["average_rating"] == 4.5


def test_calculate_rating_distribution(client, db):
    _, student_profile_1, need_1, headers_1 = _create_test_student(db, "s_dst1@test.com")
    _, student_profile_2, need_2, headers_2 = _create_test_student(db, "s_dst2@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_dst@test.com")

    session_1 = _create_completed_session(db, student_profile_1, tutor_profile, need_1)
    session_2 = _create_completed_session(db, student_profile_2, tutor_profile, need_2)

    client.post(f"/api/reviews/{session_1.id}", json={"rating": 5}, headers=headers_1)
    client.post(f"/api/reviews/{session_2.id}", json={"rating": 5}, headers=headers_2)

    res = client.get(f"/api/reviews/tutor/{tutor_profile.id}/summary")
    assert res.status_code == status.HTTP_200_OK
    dist = res.json()["rating_distribution"]
    assert dist["5"] == 2
    assert dist["4"] == 0
    assert dist["3"] == 0
    assert dist["2"] == 0
    assert dist["1"] == 0


def test_retrieve_session_review(client, db):
    _, student_profile, need, student_headers = _create_test_student(db, "s_srev@test.com")
    _, tutor_profile, tutor_headers = _create_test_tutor(db, "t_srev@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    client.post(f"/api/reviews/{session.id}", json={"rating": 5, "review_text": "Loved it"}, headers=student_headers)

    # Student can retrieve
    res_s = client.get(f"/api/reviews/session/{session.id}", headers=student_headers)
    assert res_s.status_code == status.HTTP_200_OK
    assert res_s.json()["rating"] == 5

    # Assigned tutor can retrieve
    res_t = client.get(f"/api/reviews/session/{session.id}", headers=tutor_headers)
    assert res_t.status_code == status.HTTP_200_OK
    assert res_t.json()["rating"] == 5


def test_verify_cross_user_access_protection(client, db):
    _, student_profile_a, need_a, headers_a = _create_test_student(db, "s_priv_a@test.com")
    _, student_profile_b, _, headers_b = _create_test_student(db, "s_priv_b@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_priv@test.com")

    session = _create_completed_session(db, student_profile_a, tutor_profile, need_a)
    client.post(f"/api/reviews/{session.id}", json={"rating": 5}, headers=headers_a)

    # Unrelated student B tries to access session review
    res = client.get(f"/api/reviews/session/{session.id}", headers=headers_b)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_verify_review_does_not_modify_session_status(client, db):
    _, student_profile, need, headers = _create_test_student(db, "s_stat@test.com")
    _, tutor_profile, _ = _create_test_tutor(db, "t_stat@test.com")
    session = _create_completed_session(db, student_profile, tutor_profile, need)

    res = client.post(f"/api/reviews/{session.id}", json={"rating": 5, "review_text": "Great session"}, headers=headers)
    assert res.status_code == status.HTTP_201_CREATED

    db.refresh(session)
    assert session.status == "COMPLETED"
    assert session.actual_duration_minutes == 60
    assert session.completion_note == "Covered consensus and completed session."
