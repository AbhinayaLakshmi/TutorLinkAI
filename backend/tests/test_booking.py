import uuid
from datetime import date, time, timedelta, datetime
import pytest
from fastapi import status

from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.models.student import StudentProfile, LearningNeed
from backend.app.models.tutor import TutorProfile, Availability, TutorExpertise
from backend.app.models.booking import Booking


def _create_test_student(db, email="student_booking@example.com", name="Test Student"):
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
        title="Advanced Python Programming",
        subjects=["Python", "Data Structures"],
        topics=["Trees", "Graphs"],
        learning_goals="Master algorithmic problem solving",
        preferred_availability="Weekdays 18:00 - 20:00",
        budget_min=400.0,
        budget_max=800.0,
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
    email="tutor_booking@example.com",
    name="Verified Tutor",
    verification_status="VERIFIED",
    hourly_rate=650.0,
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
        day_of_week="Monday",
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


# =====================================================================
# 1. AUTHORIZATION TESTS
# =====================================================================

def test_unauthenticated_booking_access_rejected(client):
    res = client.post("/api/booking", json={})
    assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    res_student = client.get("/api/booking/student")
    assert res_student.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    res_tutor = client.get("/api/booking/tutor/requests")
    assert res_tutor.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_tutor_cannot_create_student_booking(client, db):
    _, tutor_profile, tutor_headers = _create_test_tutor(db)
    _, target_tutor, _ = _create_test_tutor(db, email="target_tutor@example.com")

    payload = {
        "tutor_id": target_tutor.id,
        "learning_need_id": str(uuid.uuid4()),
        "scheduled_date": "2026-10-15",
        "start_time": "10:00",
        "duration_minutes": 60,
    }
    res = client.post("/api/booking", json=payload, headers=tutor_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_student_cannot_access_tutor_incoming_requests(client, db):
    _, _, _, student_headers = _create_test_student(db)
    res = client.get("/api/booking/tutor/requests", headers=student_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_tutor_cannot_access_student_bookings(client, db):
    _, _, tutor_headers = _create_test_tutor(db)
    res = client.get("/api/booking/student", headers=tutor_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


# =====================================================================
# 2. BOOKING CREATION & SERVER-SIDE SNAPSHOT
# =====================================================================

def test_student_creates_booking_successfully(client, db):
    student_user, student_profile, need, student_headers = _create_test_student(db)
    _, tutor_profile, _ = _create_test_tutor(db, hourly_rate=750.0)

    payload = {
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-20",
        "start_time": "14:00",
        "duration_minutes": 90,
        "student_message": "Looking forward to learning binary search trees!",
    }

    res = client.post("/api/booking", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()

    assert data["student_id"] == student_profile.id
    assert data["tutor_id"] == tutor_profile.id
    assert data["learning_need_id"] == need.id
    assert data["learning_need_title"] == "Advanced Python Programming"
    assert data["scheduled_date"] == "2026-10-20"
    assert data["start_time"] == "14:00"
    assert data["duration_minutes"] == 90
    assert data["status"] == "PENDING"
    assert float(data["hourly_rate"]) == 750.0
    # 750 * (90/60) = 1125.00
    assert float(data["total_amount"]) == 1125.0
    assert data["student_message"] == "Looking forward to learning binary search trees!"


def test_hourly_rate_is_server_captured_and_not_client_controlled(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, tutor_profile, _ = _create_test_tutor(db, hourly_rate=500.0)

    # Client tries to pass a lower rate
    payload = {
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-21",
        "start_time": "15:00",
        "duration_minutes": 60,
        "hourly_rate": 50.0, # Client attempt to override
    }

    res = client.post("/api/booking", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    # Must use tutor's actual rate 500.0
    assert float(data["hourly_rate"]) == 500.0
    assert float(data["total_amount"]) == 500.0


def test_cannot_book_unverified_tutor(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, unverified_tutor, _ = _create_test_tutor(
        db,
        email="unverified_tutor@example.com",
        verification_status="PENDING",
    )

    payload = {
        "tutor_id": unverified_tutor.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-22",
        "start_time": "10:00",
        "duration_minutes": 60,
    }

    res = client.post("/api/booking", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "verified" in res.json()["detail"].lower()


def test_cannot_book_nonexistent_tutor(client, db):
    _, _, need, student_headers = _create_test_student(db)
    payload = {
        "tutor_id": str(uuid.uuid4()),
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-22",
        "start_time": "10:00",
        "duration_minutes": 60,
    }
    res = client.post("/api/booking", json=payload, headers=student_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_cannot_use_another_students_learning_need(client, db):
    _, _, need_s1, _ = _create_test_student(db, email="student1@example.com")
    _, _, _, student2_headers = _create_test_student(db, email="student2@example.com")
    _, tutor_profile, _ = _create_test_tutor(db)

    payload = {
        "tutor_id": tutor_profile.id,
        "learning_need_id": need_s1.id,
        "scheduled_date": "2026-10-23",
        "start_time": "11:00",
        "duration_minutes": 60,
    }

    res = client.post("/api/booking", json=payload, headers=student2_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


def test_cannot_self_book(client, db):
    user = User(
        email="dual_role@example.com",
        hashed_password="hashedpassword123",
        full_name="Dual Role User",
        phone_number="9876543299",
        role="STUDENT",
        email_verified=True,
        onboarding_status="COMPLETED",
    )
    db.add(user)
    db.flush()

    s_prof = StudentProfile(user_id=user.id, location="Chennai")
    db.add(s_prof)
    db.flush()

    need = LearningNeed(
        student_profile_id=s_prof.id,
        title="Self Learn",
        subjects=["Math"],
        is_active=True,
    )
    db.add(need)
    db.flush()

    t_prof = TutorProfile(user_id=user.id, location="Chennai", verification_status="VERIFIED")
    db.add(t_prof)
    db.commit()

    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "tutor_id": t_prof.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-24",
        "start_time": "12:00",
        "duration_minutes": 60,
    }

    res = client.post("/api/booking", json=payload, headers=headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot book yourself" in res.json()["detail"].lower()


# =====================================================================
# 3. DUPLICATE PROTECTION
# =====================================================================

def test_duplicate_active_booking_rejected(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, tutor_profile, _ = _create_test_tutor(db)

    payload = {
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-25",
        "start_time": "16:00",
        "duration_minutes": 60,
    }

    # First request succeeds
    res1 = client.post("/api/booking", json=payload, headers=student_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    # Duplicate active request at same date/time rejected
    res2 = client.post("/api/booking", json=payload, headers=student_headers)
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "active booking request" in res2.json()["detail"].lower()


# =====================================================================
# 4. VIEWING BOOKINGS & ISOLATION
# =====================================================================

def test_student_and_tutor_booking_views_and_isolation(client, db):
    _, student1_profile, need1, student1_headers = _create_test_student(db, email="s1_view@example.com")
    _, _, need2, student2_headers = _create_test_student(db, email="s2_view@example.com")
    _, tutor1_profile, tutor1_headers = _create_test_tutor(db, email="t1_view@example.com")
    _, tutor2_profile, tutor2_headers = _create_test_tutor(db, email="t2_view@example.com")

    # Student 1 books Tutor 1
    res1 = client.post("/api/booking", json={
        "tutor_id": tutor1_profile.id,
        "learning_need_id": need1.id,
        "scheduled_date": "2026-10-26",
        "start_time": "09:00",
        "duration_minutes": 60,
    }, headers=student1_headers)
    assert res1.status_code == status.HTTP_201_CREATED

    # Student 2 books Tutor 2
    res2 = client.post("/api/booking", json={
        "tutor_id": tutor2_profile.id,
        "learning_need_id": need2.id,
        "scheduled_date": "2026-10-26",
        "start_time": "10:00",
        "duration_minutes": 60,
    }, headers=student2_headers)
    assert res2.status_code == status.HTTP_201_CREATED

    # Student 1 sees only their booking
    s1_bookings = client.get("/api/booking/student", headers=student1_headers).json()
    assert len(s1_bookings) == 1
    assert s1_bookings[0]["student_id"] == student1_profile.id
    assert s1_bookings[0]["tutor_id"] == tutor1_profile.id

    # Tutor 1 sees only Student 1's request
    t1_requests = client.get("/api/booking/tutor/requests", headers=tutor1_headers).json()
    assert len(t1_requests) == 1
    assert t1_requests[0]["tutor_id"] == tutor1_profile.id
    assert t1_requests[0]["student_id"] == student1_profile.id

    # Tutor 2 sees only Student 2's request
    t2_requests = client.get("/api/booking/tutor/requests", headers=tutor2_headers).json()
    assert len(t2_requests) == 1
    assert t2_requests[0]["tutor_id"] == tutor2_profile.id


# =====================================================================
# 5. TUTOR ACCEPT / REJECT DECISIONS
# =====================================================================

def test_tutor_accept_pending_booking(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, tutor_profile, tutor_headers = _create_test_tutor(db)

    create_res = client.post("/api/booking", json={
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-27",
        "start_time": "14:00",
        "duration_minutes": 60,
    }, headers=student_headers)
    booking_id = create_res.json()["id"]

    # Tutor accepts
    res = client.post(
        f"/api/booking/{booking_id}/decision",
        json={"decision": "ACCEPTED"},
        headers=tutor_headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "CONFIRMED"


def test_tutor_reject_pending_booking(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, tutor_profile, tutor_headers = _create_test_tutor(db)

    create_res = client.post("/api/booking", json={
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-28",
        "start_time": "15:00",
        "duration_minutes": 60,
    }, headers=student_headers)
    booking_id = create_res.json()["id"]

    # Tutor rejects
    res = client.post(
        f"/api/booking/{booking_id}/decision",
        json={"decision": "REJECTED"},
        headers=tutor_headers,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["status"] == "REJECTED"


def test_wrong_tutor_cannot_decide_booking(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, tutor1_profile, _ = _create_test_tutor(db, email="t1_wrong@example.com")
    _, _, tutor2_headers = _create_test_tutor(db, email="t2_wrong@example.com")

    create_res = client.post("/api/booking", json={
        "tutor_id": tutor1_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-29",
        "start_time": "11:00",
        "duration_minutes": 60,
    }, headers=student_headers)
    booking_id = create_res.json()["id"]

    # Tutor 2 tries to decide Tutor 1's booking
    res = client.post(
        f"/api/booking/{booking_id}/decision",
        json={"decision": "ACCEPTED"},
        headers=tutor2_headers,
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_cannot_decide_already_decided_booking(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, tutor_profile, tutor_headers = _create_test_tutor(db)

    create_res = client.post("/api/booking", json={
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-10-30",
        "start_time": "12:00",
        "duration_minutes": 60,
    }, headers=student_headers)
    booking_id = create_res.json()["id"]

    # Accept once
    res1 = client.post(
        f"/api/booking/{booking_id}/decision",
        json={"decision": "ACCEPTED"},
        headers=tutor_headers,
    )
    assert res1.status_code == status.HTTP_200_OK

    # Try to reject afterwards (invalid transition CONFIRMED -> REJECTED)
    res2 = client.post(
        f"/api/booking/{booking_id}/decision",
        json={"decision": "REJECTED"},
        headers=tutor_headers,
    )
    assert res2.status_code == status.HTTP_400_BAD_REQUEST
    assert "only pending" in res2.json()["detail"].lower()


# =====================================================================
# 6. CANCELLATION
# =====================================================================

def test_student_can_cancel_pending_booking(client, db):
    _, _, need, student_headers = _create_test_student(db)
    _, tutor_profile, _ = _create_test_tutor(db)

    create_res = client.post("/api/booking", json={
        "tutor_id": tutor_profile.id,
        "learning_need_id": need.id,
        "scheduled_date": "2026-11-01",
        "start_time": "14:00",
        "duration_minutes": 60,
    }, headers=student_headers)
    booking_id = create_res.json()["id"]

    cancel_res = client.post(
        f"/api/booking/{booking_id}/cancel",
        json={"reason": "Schedule conflict"},
        headers=student_headers,
    )
    assert cancel_res.status_code == status.HTTP_200_OK
    assert cancel_res.json()["status"] == "CANCELLED"


def test_student_cannot_cancel_another_students_booking(client, db):
    _, _, need1, student1_headers = _create_test_student(db, email="s1_cancel@example.com")
    _, _, _, student2_headers = _create_test_student(db, email="s2_cancel@example.com")
    _, tutor_profile, _ = _create_test_tutor(db)

    create_res = client.post("/api/booking", json={
        "tutor_id": tutor_profile.id,
        "learning_need_id": need1.id,
        "scheduled_date": "2026-11-02",
        "start_time": "15:00",
        "duration_minutes": 60,
    }, headers=student1_headers)
    booking_id = create_res.json()["id"]

    cancel_res = client.post(
        f"/api/booking/{booking_id}/cancel",
        json={"reason": "Malicious cancellation attempt"},
        headers=student2_headers,
    )
    assert cancel_res.status_code == status.HTTP_403_FORBIDDEN
