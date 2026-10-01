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


def _create_test_student(db, email="student_session@example.com", name="Session Student"):
    user = User(
        email=email,
        hashed_password="hashedpassword123",
        full_name=name,
        phone_number="9876543210",
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
        title="Distributed Systems & Algorithms",
        subjects=["Computer Science", "Algorithms"],
        topics=["Consensus", "Raft", "Paxos"],
        learning_goals="Master distributed consensus algorithms",
        preferred_availability="Weekdays 18:00 - 20:00",
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
    email="tutor_session@example.com",
    name="Verified Session Tutor",
    verification_status="VERIFIED",
    hourly_rate=700.0,
):
    user = User(
        email=email,
        hashed_password="hashedpassword123",
        full_name=name,
        phone_number="9876543211",
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
        verification_status=verification_status,
        languages_spoken=["English"],
    )
    db.add(profile)
    db.flush()

    availability = Availability(
        tutor_profile_id=profile.id,
        day_of_week="Tuesday",
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


def _create_confirmed_booking_and_session(client, db):
    student_user, student_profile, need, student_headers = _create_test_student(db)
    tutor_user, tutor_profile, tutor_headers = _create_test_tutor(db)

    # 1. Student creates booking request
    create_res = client.post("/api/booking", json={
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-25",
        "start_time": "15:00",
        "duration_minutes": 60,
        "student_message": "Need deep dive into Paxos.",
    }, headers=student_headers)
    assert create_res.status_code == status.HTTP_201_CREATED
    booking_id = create_res.json()["id"]

    # 2. Tutor accepts booking request
    decision_res = client.post(f"/api/booking/{booking_id}/decision", json={
        "decision": "ACCEPTED"
    }, headers=tutor_headers)
    assert decision_res.status_code == status.HTTP_200_OK

    # 3. Retrieve created session from DB
    session = db.query(SessionModel).filter(SessionModel.booking_id == booking_id).first()
    assert session is not None
    assert session.status == "SCHEDULED"

    return {
        "student_user": student_user,
        "student_profile": student_profile,
        "need": need,
        "student_headers": student_headers,
        "tutor_user": tutor_user,
        "tutor_profile": tutor_profile,
        "tutor_headers": tutor_headers,
        "booking_id": booking_id,
        "session_id": session.id,
        "session": session,
    }


# =====================================================================
# 1. UNAUTHENTICATED & ROLE ACCESS TESTS
# =====================================================================

def test_unauthenticated_access_rejected(client):
    res_student = client.get("/api/session/student")
    assert res_student.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    res_tutor = client.get("/api/session/tutor")
    assert res_tutor.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    res_detail = client.get(f"/api/session/{uuid.uuid4()}")
    assert res_detail.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_student_cannot_access_tutor_sessions_endpoint(client, db):
    _, _, _, student_headers = _create_test_student(db)
    res = client.get("/api/session/tutor", headers=student_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_tutor_cannot_access_student_sessions_endpoint(client, db):
    _, _, tutor_headers = _create_test_tutor(db)
    res = client.get("/api/session/student", headers=tutor_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


# =====================================================================
# 2. SESSION CREATION UPON BOOKING ACCEPTANCE
# =====================================================================

def test_session_is_created_when_tutor_accepts_valid_booking(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)
    session = ctx["session"]

    assert session.booking_id == ctx["booking_id"]
    assert session.student_id == ctx["student_profile"].id
    assert session.tutor_id == ctx["tutor_profile"].id
    assert session.learning_need_id == ctx["need"].id
    assert session.scheduled_date == "2026-10-25"
    assert session.start_time == "15:00"
    assert session.duration_minutes == 60
    assert session.status == "SCHEDULED"


def test_session_is_not_created_for_rejected_booking(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, tutor_profile, tutor_headers = _create_test_tutor(db)

    create_res = client.post("/api/booking", json={
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-26",
        "start_time": "10:00",
        "duration_minutes": 60,
    }, headers=student_headers)
    booking_id = create_res.json()["id"]

    # Reject
    res = client.post(f"/api/booking/{booking_id}/decision", json={"decision": "REJECTED"}, headers=tutor_headers)
    assert res.status_code == status.HTTP_200_OK

    session = db.query(SessionModel).filter(SessionModel.booking_id == booking_id).first()
    assert session is None


def test_session_is_not_created_for_cancelled_booking(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, tutor_profile, _ = _create_test_tutor(db)

    create_res = client.post("/api/booking", json={
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-27",
        "start_time": "11:00",
        "duration_minutes": 60,
    }, headers=student_headers)
    booking_id = create_res.json()["id"]

    # Cancel while pending
    res = client.post(f"/api/booking/{booking_id}/cancel", json={"reason": "No longer needed"}, headers=student_headers)
    assert res.status_code == status.HTTP_200_OK

    session = db.query(SessionModel).filter(SessionModel.booking_id == booking_id).first()
    assert session is None


def test_session_is_not_duplicated_when_booking_acceptance_is_repeated_or_invalid(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)
    booking_id = ctx["booking_id"]

    # Try accepting again
    res = client.post(f"/api/booking/{booking_id}/decision", json={"decision": "ACCEPTED"}, headers=ctx["tutor_headers"])
    assert res.status_code == status.HTTP_400_BAD_REQUEST

    sessions = db.query(SessionModel).filter(SessionModel.booking_id == booking_id).all()
    assert len(sessions) == 1


# =====================================================================
# 3. SESSION RETRIEVAL & ISOLATION
# =====================================================================

def test_student_and_tutor_can_retrieve_own_sessions_and_isolation(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)

    # Student retrieves sessions
    s_res = client.get("/api/session/student", headers=ctx["student_headers"])
    assert s_res.status_code == status.HTTP_200_OK
    s_data = s_res.json()
    assert len(s_data) == 1
    assert s_data[0]["id"] == ctx["session_id"]
    assert s_data[0]["tutor_name"] == ctx["tutor_user"].full_name
    assert s_data[0]["learning_need_title"] == ctx["need"].title

    # Tutor retrieves sessions
    t_res = client.get("/api/session/tutor", headers=ctx["tutor_headers"])
    assert t_res.status_code == status.HTTP_200_OK
    t_data = t_res.json()
    assert len(t_data) == 1
    assert t_data[0]["id"] == ctx["session_id"]
    assert t_data[0]["student_name"] == ctx["student_user"].full_name

    # Detail endpoint accessible by student & tutor
    d1 = client.get(f"/api/session/{ctx['session_id']}", headers=ctx["student_headers"])
    assert d1.status_code == status.HTTP_200_OK
    d2 = client.get(f"/api/session/{ctx['session_id']}", headers=ctx["tutor_headers"])
    assert d2.status_code == status.HTTP_200_OK


def test_user_cannot_retrieve_another_users_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)
    _, _, _, unrelated_student_headers = _create_test_student(db, email="other_student@example.com")
    _, _, unrelated_tutor_headers = _create_test_tutor(db, email="other_tutor@example.com")

    # Unrelated student cannot view
    res1 = client.get(f"/api/session/{ctx['session_id']}", headers=unrelated_student_headers)
    assert res1.status_code == status.HTTP_403_FORBIDDEN

    # Unrelated tutor cannot view
    res2 = client.get(f"/api/session/{ctx['session_id']}", headers=unrelated_tutor_headers)
    assert res2.status_code == status.HTTP_403_FORBIDDEN


# =====================================================================
# 4. SESSION START LIFECYCLE
# =====================================================================

def test_tutor_can_start_scheduled_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)

    res = client.post(f"/api/session/{ctx['session_id']}/start", headers=ctx["tutor_headers"])
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["started_at"] is not None


def test_student_cannot_start_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)
    res = client.post(f"/api/session/{ctx['session_id']}/start", headers=ctx["student_headers"])
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_cannot_start_an_already_started_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)

    # Start first time
    res1 = client.post(f"/api/session/{ctx['session_id']}/start", headers=ctx["tutor_headers"])
    assert res1.status_code == status.HTTP_200_OK

    # Start second time
    res2 = client.post(f"/api/session/{ctx['session_id']}/start", headers=ctx["tutor_headers"])
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "only scheduled" in res2.json()["detail"].lower()


# =====================================================================
# 5. SESSION COMPLETION LIFECYCLE
# =====================================================================

def test_tutor_cannot_complete_a_scheduled_session_directly(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)

    res = client.post(f"/api/session/{ctx['session_id']}/complete", json={
        "completion_note": "Completed without starting."
    }, headers=ctx["tutor_headers"])
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "only in_progress" in res.json()["detail"].lower()


def test_tutor_can_complete_an_in_progress_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)

    # 1. Start session
    start_res = client.post(f"/api/session/{ctx['session_id']}/start", headers=ctx["tutor_headers"])
    assert start_res.status_code == status.HTTP_200_OK

    # 2. Complete session with completion note
    complete_res = client.post(f"/api/session/{ctx['session_id']}/complete", json={
        "completion_note": "Covered Raft leader election and log replication."
    }, headers=ctx["tutor_headers"])
    assert complete_res.status_code == status.HTTP_200_OK
    data = complete_res.json()

    assert data["status"] == "COMPLETED"
    assert data["ended_at"] is not None
    assert data["actual_duration_minutes"] >= 1
    assert data["completion_note"] == "Covered Raft leader election and log replication."


def test_actual_duration_is_calculated_server_side(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)

    # Set started_at back by 45 minutes manually in db
    session = db.query(SessionModel).filter(SessionModel.id == ctx["session_id"]).first()
    session.status = "IN_PROGRESS"
    session.started_at = datetime.utcnow() - timedelta(minutes=45)
    db.commit()

    complete_res = client.post(f"/api/session/{ctx['session_id']}/complete", json={
        "completion_note": "45-minute deep dive."
    }, headers=ctx["tutor_headers"])
    assert complete_res.status_code == status.HTTP_200_OK
    data = complete_res.json()

    assert data["actual_duration_minutes"] == 45


def test_student_cannot_complete_a_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)
    client.post(f"/api/session/{ctx['session_id']}/start", headers=ctx["tutor_headers"])

    res = client.post(f"/api/session/{ctx['session_id']}/complete", json={
        "completion_note": "Student attempt"
    }, headers=ctx["student_headers"])
    assert res.status_code == status.HTTP_403_FORBIDDEN


# =====================================================================
# 6. SESSION CANCELLATION
# =====================================================================

def test_student_can_cancel_a_scheduled_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)

    res = client.post(f"/api/session/{ctx['session_id']}/cancel", json={
        "reason": "Family emergency."
    }, headers=ctx["student_headers"])
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "CANCELLED"
    assert data["cancellation_reason"] == "Family emergency."


def test_tutor_can_cancel_a_scheduled_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)

    res = client.post(f"/api/session/{ctx['session_id']}/cancel", json={
        "reason": "Illness."
    }, headers=ctx["tutor_headers"])
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["status"] == "CANCELLED"
    assert data["cancellation_reason"] == "Illness."


def test_cannot_cancel_an_in_progress_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)
    client.post(f"/api/session/{ctx['session_id']}/start", headers=ctx["tutor_headers"])

    res = client.post(f"/api/session/{ctx['session_id']}/cancel", json={
        "reason": "Too late to cancel"
    }, headers=ctx["student_headers"])
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "only scheduled" in res.json()["detail"].lower()


def test_cannot_cancel_a_completed_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)
    client.post(f"/api/session/{ctx['session_id']}/start", headers=ctx["tutor_headers"])
    client.post(f"/api/session/{ctx['session_id']}/complete", json={}, headers=ctx["tutor_headers"])

    res = client.post(f"/api/session/{ctx['session_id']}/cancel", json={
        "reason": "Attempting to cancel finished session"
    }, headers=ctx["tutor_headers"])
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "only scheduled" in res.json()["detail"].lower()


def test_cannot_modify_another_users_session(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)
    _, _, other_tutor_headers = _create_test_tutor(db, email="other_tutor2@example.com")

    # Other tutor cannot start
    res_start = client.post(f"/api/session/{ctx['session_id']}/start", headers=other_tutor_headers)
    assert res_start.status_code == status.HTTP_403_FORBIDDEN

    # Other tutor cannot cancel
    res_cancel = client.post(f"/api/session/{ctx['session_id']}/cancel", json={}, headers=other_tutor_headers)
    assert res_cancel.status_code == status.HTTP_403_FORBIDDEN


def test_invalid_status_transitions_are_rejected(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)

    # Cancel scheduled session
    client.post(f"/api/session/{ctx['session_id']}/cancel", json={}, headers=ctx["tutor_headers"])

    # Cannot start cancelled session
    res_start = client.post(f"/api/session/{ctx['session_id']}/start", headers=ctx["tutor_headers"])
    assert res_start.status_code == status.HTTP_400_BAD_REQUEST

    # Cannot complete cancelled session
    res_complete = client.post(f"/api/session/{ctx['session_id']}/complete", json={}, headers=ctx["tutor_headers"])
    assert res_complete.status_code == status.HTTP_400_BAD_REQUEST


def test_learning_need_traceability_and_ownership_consistency(client, db):
    ctx = _create_confirmed_booking_and_session(client, db)
    session = ctx["session"]

    # Session correctly references the learning need and profiles
    assert session.learning_need_id == ctx["need"].id
    assert session.student_id == ctx["student_profile"].id
    assert session.tutor_id == ctx["tutor_profile"].id
    assert session.booking_id == ctx["booking_id"]

    # API output contains learning need title
    res = client.get(f"/api/session/{session.id}", headers=ctx["student_headers"])
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["learning_need_title"] == "Distributed Systems & Algorithms"
    assert data["tutor_name"] == ctx["tutor_user"].full_name
    assert data["student_name"] == ctx["student_user"].full_name
