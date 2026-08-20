import io
from datetime import datetime, timedelta
from fastapi import status
import pytest
from backend.app.core.config import settings
from backend.app.models.user import OTPVerification
from backend.app.services.email import send_otp_email

def test_register_student_success(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "student@example.com",
            "password": "StrongPassword123!",
            "full_name": "John Student",
            "phone_number": "1234567890",
            "role": "STUDENT"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "student@example.com"
    assert data["role"] == "STUDENT"
    assert data["email_verified"] is False
    assert data["onboarding_status"] == "INCOMPLETE"
    assert "student@example.com" in settings.TEST_OTP_STORE

def test_register_invalid_password(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "student@example.com",
            "password": "simple",  # under 8 chars, no caps, no spec
            "full_name": "John Student",
            "phone_number": "1234567890",
            "role": "STUDENT"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_register_invalid_phone(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "student@example.com",
            "password": "StrongPassword123!",
            "full_name": "John Student",
            "phone_number": "12345",  # less than 10 digits
            "role": "STUDENT"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_register_duplicate_email(client):
    user_data = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123!",
        "full_name": "Test User",
        "phone_number": "1234567890",
        "role": "STUDENT"
    }
    client.post("/api/auth/register", json=user_data)
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Email already registered."

def test_otp_verification_lifecycle(client, db):
    # 1. Register user
    email = "otp@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "OTP User",
            "phone_number": "9876543210",
            "role": "STUDENT"
        }
    )
    
    # Extract plain OTP from mock store
    plain_otp = settings.TEST_OTP_STORE[email]
    
    # 2. Try invalid OTP
    res_bad = client.post(
        "/api/auth/verify-otp",
        json={"email": email, "otp": "000000"}
    )
    assert res_bad.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid OTP code" in res_bad.json()["detail"]
    
    # 3. Test OTP resend rate limit (cooldown)
    res_resend_bad = client.post("/api/auth/resend-otp", json={"email": email})
    assert res_resend_bad.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    # 4. Verify OTP Expired check
    otp_record = db.query(OTPVerification).first()
    otp_record.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    
    res_expired = client.post(
        "/api/auth/verify-otp",
        json={"email": email, "otp": plain_otp}
    )
    assert res_expired.status_code == status.HTTP_400_BAD_REQUEST
    assert "expired" in res_expired.json()["detail"].lower()
    
    # 5. Resend OTP after expiration/deletion
    res_resend = client.post("/api/auth/resend-otp", json={"email": email})
    assert res_resend.status_code == status.HTTP_200_OK
    new_otp = settings.TEST_OTP_STORE[email]
    
    # 6. Verify success OTP
    res_verify = client.post(
        "/api/auth/verify-otp",
        json={"email": email, "otp": new_otp}
    )
    assert res_verify.status_code == status.HTTP_200_OK
    data = res_verify.json()
    assert "access_token" in data
    assert data["user"]["email_verified"] is True

def test_otp_attempt_limits(client, db):
    email = "limit@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Limit User",
            "phone_number": "1234567890",
            "role": "STUDENT"
        }
    )
    
    # Submit wrong OTP 5 times
    for i in range(5):
        res = client.post(
            "/api/auth/verify-otp",
            json={"email": email, "otp": "000000"}
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        
    # The 6th attempt should state "No active OTP found" because it got deleted on limit
    res_final = client.post(
        "/api/auth/verify-otp",
        json={"email": email, "otp": "000000"}
    )
    assert res_final.status_code == status.HTTP_400_BAD_REQUEST
    assert "No active OTP" in res_final.json()["detail"]

def test_student_school_flow(client):
    # Register & Verify
    email = "school@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "School Student",
            "phone_number": "1122334455",
            "role": "STUDENT"
        }
    )
    otp = settings.TEST_OTP_STORE[email]
    login_res = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Save School details
    update_res = client.put(
        "/api/onboarding/student/me",
        headers=headers,
        json={
            "student_type": "SCHOOL",
            "school_board": "CBSE",
            "grade": "Class 10",
            "school_name": "Saint Mary School",
            "location": "New Delhi",
            "preferred_learning_mode": "Online",
            "preferred_tutor_languages": ["Hindi", "English"],
            "requirements": {
                "subjects": ["Science"],
                "topics": ["Physics"],
                "learning_goals": "Prep for board exams"
            }
        }
    )
    assert update_res.status_code == status.HTTP_200_OK
    d = update_res.json()
    assert d["student_type"] == "SCHOOL"
    assert d["school_board"] == "CBSE"
    assert d["university"] is None
    
    # Complete
    complete_res = client.post("/api/onboarding/student/complete", headers=headers)
    assert complete_res.status_code == status.HTTP_200_OK
    assert complete_res.json()["onboarding_status"] == "COMPLETED"

def test_student_university_flow(client):
    # Register & Verify
    email = "uni@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Uni Student",
            "phone_number": "1122334455",
            "role": "STUDENT"
        }
    )
    otp = settings.TEST_OTP_STORE[email]
    login_res = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Save University details
    update_res = client.put(
        "/api/onboarding/student/me",
        headers=headers,
        json={
            "student_type": "UNIVERSITY",
            "university": "MIT",
            "course": "Mechanical Engineering",
            "year_of_study": 2,
            "specialization": "Robotics",
            "location": "Boston",
            "preferred_learning_mode": "Both",
            "preferred_tutor_languages": ["English"],
            "requirements": {
                "subjects": ["Robotics 101"],
                "topics": ["Actuators"],
                "learning_goals": "Get help with labs"
            }
        }
    )
    assert update_res.status_code == status.HTTP_200_OK
    d = update_res.json()
    assert d["student_type"] == "UNIVERSITY"
    assert d["university"] == "MIT"
    assert d["school_name"] is None
    
    # Complete
    complete_res = client.post("/api/onboarding/student/complete", headers=headers)
    assert complete_res.status_code == status.HTTP_200_OK
    assert complete_res.json()["onboarding_status"] == "COMPLETED"

def test_tutor_onboarding_and_upload_flow(client):
    # Register & Verify
    email = "tutor_flow@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Tutor User",
            "phone_number": "1122334455",
            "role": "TUTOR"
        }
    )
    otp = settings.TEST_OTP_STORE[email]
    login_res = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Save Tutor Details
    update_res = client.put(
        "/api/onboarding/tutor/me",
        headers=headers,
        json={
            "location": "Chicago",
            "languages_spoken": ["English"],
            "preferred_teaching_mode": "Both",
            "education": [
                {
                    "highest_degree": "Bachelor",
                    "degree_name": "B.Sc. Physics",
                    "university": "UChicago",
                    "graduation_year": 2019
                }
            ],
            "expertise": {
                "subjects_taught": ["Physics"],
                "topics_expertise": ["Optics"],
                "student_levels": ["High School"],
                "years_of_experience": 3,
                "skills": ["Physics Tutor"],
                "languages_can_teach_in": ["English"]
            },
            "availability": [
                {
                    "day_of_week": "Friday",
                    "time_ranges": [{"start": "13:00", "end": "16:00"}],
                    "preferred_session_duration": 60,
                    "hourly_rate": 45.0
                }
            ]
        }
    )
    assert update_res.status_code == status.HTTP_200_OK
    
    # Upload certificate
    file_payload = {"file": ("degree.png", io.BytesIO(b"image bytes data"), "image/png")}
    upload_res = client.post(
        "/api/onboarding/tutor/me/certificate",
        headers=headers,
        files=file_payload
    )
    assert upload_res.status_code == status.HTTP_200_OK
    cert_id = upload_res.json()["id"]
    
    # Complete
    complete_res = client.post("/api/onboarding/tutor/complete", headers=headers)
    assert complete_res.status_code == status.HTTP_200_OK
    assert complete_res.json()["onboarding_status"] == "COMPLETED"

def test_email_service_trigger_and_validation(client, monkeypatch):
    # 1. Test that incomplete SMTP settings raise configuration error (ValueError)
    old_host = settings.SMTP_HOST
    settings.SMTP_HOST = ""
    try:
        with pytest.raises(ValueError) as exc:
            send_otp_email("test@example.com", "123456")
        assert "SMTP email service is not configured" in str(exc.value)
    finally:
        settings.SMTP_HOST = old_host

    # 2. Test that registering a user successfully triggers the mock email sender
    # capturing the correct target email address and generating a valid 6-digit OTP code
    email = "trigger_test@example.com"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Test Trigger",
            "phone_number": "1234567890",
            "role": "STUDENT"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert email in settings.TEST_OTP_STORE
    assert len(settings.TEST_OTP_STORE[email]) == 6
    assert settings.TEST_OTP_STORE[email].isdigit()
