import pytest
import base64
import cv2
import numpy as np
import os
from fastapi import status
from starlette.testclient import TestClient

from backend.app.services.live_face import LiveFaceService
from backend.app.services.face import BaseFaceDetector

class MockStepDetector(BaseFaceDetector):
    def __init__(self, step_boxes):
        self.step_boxes = step_boxes
        self.call_count = 0
        
    def detect(self, image: np.ndarray):
        box = self.step_boxes[self.call_count % len(self.step_boxes)]
        self.call_count += 1
        return box

def make_dummy_b64_image(color=(128, 128, 128), text=None) -> str:
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:, :] = color
    if text:
        cv2.putText(img, text, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    _, buffer = cv2.imencode(".jpg", img)
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode()


def test_decode_base64_image():
    service = LiveFaceService()
    b64 = make_dummy_b64_image()
    img = service._decode_image(b64)
    assert isinstance(img, np.ndarray)
    assert img.shape == (480, 640, 3)


def test_live_face_no_face():
    # Return 0 boxes for both calls
    service = LiveFaceService(detector=MockStepDetector([[], []]))
    
    img_b64 = make_dummy_b64_image()
    res = service.verify_live_face(img_b64, img_b64, "HEAD_LEFT")
    
    assert res["face_detected"] is False
    assert res["face_count"] == 0
    assert "No face detected" in res["reason"]


def test_live_face_multiple_faces():
    # Return 2 boxes for first call
    service = LiveFaceService(detector=MockStepDetector([
        [(50, 50, 120, 120), (200, 200, 120, 120)],
        [(50, 50, 120, 120)]
    ]))
    
    img_b64 = make_dummy_b64_image()
    res = service.verify_live_face(img_b64, img_b64, "HEAD_LEFT")
    
    assert res["face_detected"] is True
    assert res["face_count"] == 2
    assert "Multiple faces" in res["reason"]


def test_live_face_too_small():
    # Return a tiny box (< 100px)
    service = LiveFaceService(detector=MockStepDetector([
        [(50, 50, 80, 80)],
        [(50, 50, 80, 80)]
    ]), min_face_dim=100)
    
    img_b64 = make_dummy_b64_image()
    res = service.verify_live_face(img_b64, img_b64, "HEAD_LEFT")
    
    assert res["face_detected"] is True
    assert res["face_count"] == 1
    assert "too far/small" in res["reason"]


def test_live_face_blurry():
    # Return box, but image is a plain gray canvas (0 blur score)
    service = LiveFaceService(detector=MockStepDetector([
        [(100, 100, 150, 150)],
        [(100, 100, 150, 150)]
    ]), max_blur_threshold=10.0)
    
    img_b64 = make_dummy_b64_image(color=(120, 120, 120))  # zero variance
    res = service.verify_live_face(img_b64, img_b64, "HEAD_LEFT")
    
    assert res["face_detected"] is True
    assert res["face_quality"] == "POOR"
    assert "too blurry" in res["reason"]


def test_live_face_static_spoof():
    # Two identical frames with high-contrast text, but identical content (MAD = 0, shift = 0)
    service = LiveFaceService(detector=MockStepDetector([
        [(100, 100, 150, 150)],
        [(100, 100, 150, 150)]
    ]), max_blur_threshold=5.0)
    
    img_b64 = make_dummy_b64_image(text="HIGH_CONTRAST_SHARP_TEXT")
    res = service.verify_live_face(img_b64, img_b64, "LEFT")
    
    assert res["face_detected"] is True
    assert res["liveness_status"] == "MANUAL_REVIEW"
    assert "No movement detected" in res["reason"]


def test_live_face_valid_left_passed():
    # Straight: center 175, Action: center 225 (shift = +50). LEFT challenge expects shift > 0 (PASS)
    service = LiveFaceService(detector=MockStepDetector([
        [(100, 100, 150, 150)],
        [(150, 100, 150, 150)]
    ]), max_blur_threshold=1.0)
    
    img_s = make_dummy_b64_image(color=(100, 100, 100), text="FRAME_1")
    img_a = make_dummy_b64_image(color=(200, 200, 200), text="FRAME_2")
    
    res = service.verify_live_face(img_s, img_a, "LEFT")
    
    assert res["face_detected"] is True
    assert res["liveness_status"] == "PASSED"
    assert res["suitable_for_matching"] is True


def test_live_face_valid_right_passed():
    # Straight: center 175, Action: center 125 (shift = -50). RIGHT challenge expects shift < 0 (PASS)
    service = LiveFaceService(detector=MockStepDetector([
        [(100, 100, 150, 150)],
        [(50, 100, 150, 150)]
    ]), max_blur_threshold=1.0)
    
    img_s = make_dummy_b64_image(color=(100, 100, 100), text="FRAME_1")
    img_a = make_dummy_b64_image(color=(200, 200, 200), text="FRAME_2")
    
    res = service.verify_live_face(img_s, img_a, "RIGHT")
    
    assert res["face_detected"] is True
    assert res["liveness_status"] == "PASSED"
    assert res["suitable_for_matching"] is True


def test_live_face_left_challenge_right_movement_fail():
    # Straight: center 175, Action: center 125 (shift = -50 -> RIGHT turn). LEFT challenge expects shift > 0 (FAIL)
    service = LiveFaceService(detector=MockStepDetector([
        [(100, 100, 150, 150)],
        [(50, 100, 150, 150)]
    ]), max_blur_threshold=1.0)
    
    img_s = make_dummy_b64_image(color=(100, 100, 100), text="FRAME_1")
    img_a = make_dummy_b64_image(color=(200, 200, 200), text="FRAME_2")
    
    res = service.verify_live_face(img_s, img_a, "LEFT")
    
    assert res["face_detected"] is True
    assert res["liveness_status"] == "FAILED"
    assert "Unexpected movement detected" in res["reason"]


def test_live_face_right_challenge_left_movement_fail():
    # Straight: center 175, Action: center 225 (shift = +50 -> LEFT turn). RIGHT challenge expects shift < 0 (FAIL)
    service = LiveFaceService(detector=MockStepDetector([
        [(100, 100, 150, 150)],
        [(150, 100, 150, 150)]
    ]), max_blur_threshold=1.0)
    
    img_s = make_dummy_b64_image(color=(100, 100, 100), text="FRAME_1")
    img_a = make_dummy_b64_image(color=(200, 200, 200), text="FRAME_2")
    
    res = service.verify_live_face(img_s, img_a, "RIGHT")
    
    assert res["face_detected"] is True
    assert res["liveness_status"] == "FAILED"
    assert "Unexpected movement detected" in res["reason"]


def test_random_challenge_generation():
    import random
    challenges = ["LEFT", "RIGHT"]
    results = [random.choice(challenges) for _ in range(100)]
    assert "LEFT" in results
    assert "RIGHT" in results


def test_api_live_face_endpoint(client: TestClient, monkeypatch):
    """
    Test the FastAPI route integration using mock authentication headers.
    """
    from backend.app.core.config import settings
    client.post(
        "/api/auth/register",
        json={
            "email": "livetutor@example.com",
            "password": "Password123!",
            "full_name": "Live Tutor",
            "phone_number": "1234567890",
            "role": "TUTOR"
        }
    )
    otp = settings.TEST_OTP_STORE["livetutor@example.com"]
    login_res = client.post("/api/auth/verify-otp", json={"email": "livetutor@example.com", "otp": otp})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Setup onboarding profile and upload mock certificate
    client.put(
        "/api/onboarding/tutor/me",
        headers=headers,
        json={
            "location": "Dallas",
            "education": [
                {
                    "highest_degree": "Master",
                    "degree_name": "Master of Computer Science",
                    "university": "UT Dallas",
                    "graduation_year": 2021
                }
            ]
        }
    )
    import io
    file_payload = {"file": ("mit_certificate.pdf", io.BytesIO(b"dummy pdf content"), "application/pdf")}
    client.post("/api/onboarding/tutor/me/certificate", headers=headers, files=file_payload)

    # 3. Start verification record pipeline
    client.post("/api/verification/tutor/me/start", headers=headers)

    # 4. Mock the LiveFaceService behavior inside routes
    class MockService:
        def verify_live_face(self, frame_straight, frame_action, action):
            return {
                "face_detected": True,
                "face_count": 1,
                "face_quality": "GOOD",
                "image_width": 640,
                "image_height": 480,
                "face_width": 150,
                "face_height": 150,
                "liveness_status": "PASSED",
                "liveness_method": "HEAD_TURN",
                "suitable_for_matching": True,
                "reason": "One clear face detected and requested live movement completed."
            }

    monkeypatch.setattr("backend.app.modules.verification.routes.LiveFaceService", MockService)

    # 5. Call endpoint
    payload = {
        "action": "HEAD_LEFT",
        "frame_straight": "data:image/jpeg;base64,dummy1",
        "frame_action": "data:image/jpeg;base64,dummy2"
    }
    
    res = client.post("/api/verification/tutor/me/live-face", headers=headers, json=payload)
    
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["face_detected"] is True
    assert data["liveness_status"] == "PASSED"


def test_liveness_transitions_to_verified(db, client, monkeypatch):
    """
    Test the status transition logic to VERIFIED under various pipelines configurations.
    """
    from backend.app.core.config import settings
    from backend.app.models.tutor import TutorProfile
    from backend.app.models.verification import VerificationRecord
    
    email = "tutor_promo@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Tutor User",
            "phone_number": "1234567890",
            "role": "TUTOR"
        }
    )
    otp = settings.TEST_OTP_STORE[email]
    login_res = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.put(
        "/api/onboarding/tutor/me",
        headers=headers,
        json={
            "location": "Boston",
            "education": [
                {
                    "highest_degree": "Bachelor",
                    "degree_name": "Bachelor of Science in Physics",
                    "university": "Massachusetts Institute of Technology",
                    "graduation_year": 2019
                }
            ]
        }
    )
    import io
    file_payload = {"file": ("mit_certificate.png", io.BytesIO(b"image bytes"), "image/png")}
    client.post("/api/onboarding/tutor/me/certificate", headers=headers, files=file_payload)

    # 1. Pipeline execution (sets ocr=COMPLETED, validation=MATCH, security=PASS)
    client.post("/api/verification/tutor/me/start", headers=headers)
    
    # Verify starting states are PENDING
    profile = db.query(TutorProfile).filter(TutorProfile.location == "Boston").first()
    record = db.query(VerificationRecord).filter(VerificationRecord.tutor_profile_id == profile.id).first()
    assert profile.verification_status == "PENDING"
    assert record.verification_status == "PENDING"
    
    # 2. Mock LiveFaceService to return PASSED
    class MockServicePassed:
        def verify_live_face(self, frame_straight, frame_action, action):
            return {
                "face_detected": True,
                "face_count": 1,
                "face_quality": "GOOD",
                "image_width": 640,
                "image_height": 480,
                "face_width": 150,
                "face_height": 150,
                "liveness_status": "PASSED",
                "liveness_method": "HEAD_TURN",
                "suitable_for_matching": True,
                "reason": "One clear face detected and requested live movement completed."
            }

    monkeypatch.setattr("backend.app.modules.verification.routes.LiveFaceService", MockServicePassed)
    
    payload = {
        "action": "LEFT",
        "frame_straight": "data:image/jpeg;base64,dummy1",
        "frame_action": "data:image/jpeg;base64,dummy2"
    }
    
    # Post liveness check
    client.post("/api/verification/tutor/me/live-face", headers=headers, json=payload)
    
    # Verify promoted to VERIFIED (both record and profile)
    db.refresh(profile)
    db.refresh(record)
    assert profile.verification_status == "VERIFIED"
    assert record.verification_status == "VERIFIED"

    # Test idempotence (submitting again keeps status as VERIFIED)
    client.post("/api/verification/tutor/me/live-face", headers=headers, json=payload)
    db.refresh(profile)
    db.refresh(record)
    assert profile.verification_status == "VERIFIED"
    assert record.verification_status == "VERIFIED"
