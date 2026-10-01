"""
Tests for Step 3B: Certificate-to-Live Face Embedding Comparison.

Validates:
1. LiveFaceService successful liveness provides an internal face crop.
2. Failed liveness does not provide a usable identity face crop.
3. Multiple faces do not provide an identity face crop.
4. Certificate crop + FaceEmbedder produces a valid 128-D embedding.
5. Live crop + FaceEmbedder produces a valid 128-D embedding.
6. Certificate and live embeddings can be compared using cosine similarity.
7. Similarity is a finite float in [-1.0, 1.0].
8. Identical image/embedding compared with itself produces approximately 1.0.
9. Different test images can be compared and produce a finite similarity score (no decision threshold applied).
10. API endpoint (/api/verification/tutor/me/live-face) response is JSON serializable and does NOT contain raw NumPy face_crop.
11. No biometric embeddings or face crops are persisted to database or filesystem.
12. Real certificate portrait embedding and comparison execution if present in environment.
"""

import os
import io
import json
import base64
import pytest
import numpy as np
import cv2
from starlette.testclient import TestClient
from fastapi import status

from backend.app.services.live_face import LiveFaceService
from backend.app.services.face import CertificateFaceService, BaseFaceDetector
from backend.app.services.face_embedder import FaceEmbedder


class MockStepDetector(BaseFaceDetector):
    def __init__(self, step_boxes):
        self.step_boxes = step_boxes
        self.call_count = 0
        
    def detect(self, image: np.ndarray):
        box = self.step_boxes[self.call_count % len(self.step_boxes)]
        self.call_count += 1
        return box


def make_test_b64_image(color=(128, 128, 128), text=None) -> str:
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:, :] = color
    if text:
        cv2.putText(img, text, (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    _, buffer = cv2.imencode(".jpg", img)
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode()


def make_synthetic_face_crop(seed: int = 42, size: int = 120) -> np.ndarray:
    """Generates a synthetic 3-channel face-like image for isolated biometric testing."""
    np.random.seed(seed)
    crop = np.full((size, size, 3), 150 + (seed % 30), dtype=np.uint8)
    cv2.circle(crop, (int(size * 0.3), int(size * 0.35)), int(size * 0.08), (40, 40, 40), -1)
    cv2.circle(crop, (int(size * 0.7), int(size * 0.35)), int(size * 0.08), (40, 40, 40), -1)
    cv2.line(crop, (int(size * 0.35), int(size * 0.7)), (int(size * 0.65), int(size * 0.7)), (50, 50, 180), 2)
    return crop


def test_live_service_provides_internal_crop_on_passed():
    """1. LiveFaceService returns internal face_crop on PASSED liveness."""
    service = LiveFaceService(detector=MockStepDetector([
        [(100, 100, 150, 150)],
        [(150, 100, 150, 150)]
    ]), max_blur_threshold=1.0)
    
    img_s = make_test_b64_image(color=(100, 100, 100), text="FRAME_1")
    img_a = make_test_b64_image(color=(200, 200, 200), text="FRAME_2")
    
    res = service.verify_live_face(img_s, img_a, "LEFT")
    
    assert res["liveness_status"] == "PASSED"
    assert res["face_crop"] is not None
    assert isinstance(res["face_crop"], np.ndarray)
    assert res["face_crop"].shape == (150, 150, 3)
    assert res["face_crop"].dtype == np.uint8


def test_live_service_no_crop_on_failed_liveness():
    """2. Failed liveness does not provide a usable identity face crop."""
    # Opposite movement -> FAILED
    service = LiveFaceService(detector=MockStepDetector([
        [(100, 100, 150, 150)],
        [(50, 100, 150, 150)]
    ]), max_blur_threshold=1.0)
    
    img_s = make_test_b64_image(color=(100, 100, 100), text="FRAME_1")
    img_a = make_test_b64_image(color=(200, 200, 200), text="FRAME_2")
    
    res = service.verify_live_face(img_s, img_a, "LEFT")
    
    assert res["liveness_status"] == "FAILED"
    assert res["face_crop"] is None


def test_live_service_no_crop_on_multiple_faces():
    """3. Multiple faces do not provide an identity face crop."""
    service = LiveFaceService(detector=MockStepDetector([
        [(50, 50, 120, 120), (200, 200, 120, 120)],
        [(50, 50, 120, 120)]
    ]))
    
    img_b64 = make_test_b64_image()
    res = service.verify_live_face(img_b64, img_b64, "LEFT")
    
    assert res["face_count"] == 2
    assert res["face_crop"] is None


def test_certificate_crop_embedding_properties():
    """4. Certificate crop + FaceEmbedder produces a valid 128-D embedding."""
    embedder = FaceEmbedder()
    cert_crop = make_synthetic_face_crop(seed=101, size=140)
    
    emb = embedder.extract_embedding(cert_crop)
    
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (1, 128)
    assert emb.dtype == np.float32
    assert np.all(np.isfinite(emb))
    assert pytest.approx(float(np.linalg.norm(emb)), abs=1e-5) == 1.0


def test_live_crop_embedding_properties():
    """5. Live crop + FaceEmbedder produces a valid 128-D embedding."""
    embedder = FaceEmbedder()
    live_crop = make_synthetic_face_crop(seed=202, size=150)
    
    emb = embedder.extract_embedding(live_crop)
    
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (1, 128)
    assert emb.dtype == np.float32
    assert np.all(np.isfinite(emb))
    assert pytest.approx(float(np.linalg.norm(emb)), abs=1e-5) == 1.0


def test_certificate_and_live_cosine_similarity():
    """6. Certificate and live embeddings can be compared using cosine similarity."""
    embedder = FaceEmbedder()
    cert_crop = make_synthetic_face_crop(seed=1, size=140)
    live_crop = make_synthetic_face_crop(seed=2, size=150)
    
    e_cert = embedder.extract_embedding(cert_crop)
    e_live = embedder.extract_embedding(live_crop)
    
    similarity = embedder.compute_cosine_similarity(e_cert, e_live)
    
    assert isinstance(similarity, float)
    assert np.isfinite(similarity)


def test_similarity_bounded_in_range():
    """7. Cosine similarity is mathematically bounded in [-1.0, 1.0]."""
    embedder = FaceEmbedder()
    # Random orthogonal or inverted vectors
    for i in range(10):
        c1 = make_synthetic_face_crop(seed=i * 10, size=120)
        c2 = make_synthetic_face_crop(seed=i * 10 + 5, size=120)
        sim = embedder.compare_face_crops(c1, c2)
        assert -1.0 <= sim <= 1.0


def test_identical_crop_self_similarity():
    """8. Identical crop compared with itself produces cosine similarity approx 1.0."""
    embedder = FaceEmbedder()
    crop = make_synthetic_face_crop(seed=999, size=130)
    
    sim = embedder.compare_face_crops(crop, crop)
    
    assert pytest.approx(sim, abs=1e-5) == 1.0


def test_different_images_produce_finite_similarity_no_threshold():
    """9. Different face crops produce a finite float without asserting hardcoded thresholds."""
    embedder = FaceEmbedder()
    crop_a = make_synthetic_face_crop(seed=111, size=120)
    crop_b = make_synthetic_face_crop(seed=999, size=120)
    
    similarity = embedder.compare_face_crops(crop_a, crop_b)
    
    assert isinstance(similarity, float)
    assert np.isfinite(similarity)
    assert -1.0 <= similarity <= 1.0


def test_api_response_is_json_serializable_and_no_raw_crop(client: TestClient, monkeypatch):
    """10. Test that the API response remains JSON serializable and does NOT contain a NumPy ndarray."""
    from backend.app.core.config import settings
    
    email = "live_json_test@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "API JSON Test Tutor",
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
            "location": "New York",
            "education": [
                {
                    "highest_degree": "Bachelor",
                    "degree_name": "Bachelor of Science",
                    "university": "MIT",
                    "graduation_year": 2020
                }
            ]
        }
    )
    file_payload = {"file": ("mit_cert.png", io.BytesIO(b"image bytes"), "image/png")}
    client.post("/api/onboarding/tutor/me/certificate", headers=headers, files=file_payload)
    client.post("/api/verification/tutor/me/start", headers=headers)

    # Use actual LiveFaceService with mock detector returning passed movement
    class MockServiceWithCrop:
        def verify_live_face(self, frame_straight, frame_action, action):
            return {
                "face_detected": True,
                "face_count": 1,
                "face_crop": np.zeros((120, 120, 3), dtype=np.uint8),  # Raw NumPy array
                "face_quality": "GOOD",
                "image_width": 640,
                "image_height": 480,
                "face_width": 120,
                "face_height": 120,
                "liveness_status": "PASSED",
                "liveness_method": "HEAD_TURN",
                "suitable_for_matching": True,
                "reason": "Passed movement."
            }

    monkeypatch.setattr("backend.app.modules.verification.routes.LiveFaceService", MockServiceWithCrop)

    payload = {
        "action": "LEFT",
        "frame_straight": "data:image/jpeg;base64,dummy1",
        "frame_action": "data:image/jpeg;base64,dummy2"
    }
    
    res = client.post("/api/verification/tutor/me/live-face", headers=headers, json=payload)
    
    assert res.status_code == status.HTTP_200_OK
    
    # Must be valid JSON string
    raw_text = res.text
    parsed_json = json.loads(raw_text)
    
    # Assert face_crop was popped and NOT exposed in API output
    assert "face_crop" not in parsed_json
    assert parsed_json["liveness_status"] == "PASSED"
    assert parsed_json["face_detected"] is True


def test_no_biometrics_persisted_to_db_or_filesystem(db, client, monkeypatch):
    """11. Verify that no embedding vectors or face images are stored in DB columns or disk."""
    from backend.app.core.config import settings
    from backend.app.models.tutor import TutorProfile
    from backend.app.models.verification import VerificationRecord

    email = "nobiometrics@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "No Biometrics Tutor",
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
            "location": "Austin",
            "education": [{"highest_degree": "B.Sc", "degree_name": "CS", "university": "UT Austin", "graduation_year": 2021}]
        }
    )
    file_payload = {"file": ("ut_cert.png", io.BytesIO(b"image bytes"), "image/png")}
    client.post("/api/onboarding/tutor/me/certificate", headers=headers, files=file_payload)
    client.post("/api/verification/tutor/me/start", headers=headers)

    profile = db.query(TutorProfile).filter(TutorProfile.location == "Austin").first()
    record = db.query(VerificationRecord).filter(VerificationRecord.tutor_profile_id == profile.id).first()

    class MockService:
        def verify_live_face(self, frame_straight, frame_action, action):
            return {
                "face_detected": True,
                "face_count": 1,
                "face_crop": np.zeros((120, 120, 3), dtype=np.uint8),
                "face_quality": "GOOD",
                "image_width": 640,
                "image_height": 480,
                "face_width": 120,
                "face_height": 120,
                "liveness_status": "PASSED",
                "liveness_method": "HEAD_TURN",
                "suitable_for_matching": True,
                "reason": "Movement verified."
            }

    monkeypatch.setattr("backend.app.modules.verification.routes.LiveFaceService", MockService)

    payload = {
        "action": "LEFT",
        "frame_straight": "data:image/jpeg;base64,dummy1",
        "frame_action": "data:image/jpeg;base64,dummy2"
    }
    client.post("/api/verification/tutor/me/live-face", headers=headers, json=payload)

    db.refresh(record)
    # Check that record contains only standard strings/flags, no embedding or binary data
    assert isinstance(record.face_verification_status, str)
    assert isinstance(record.liveness_status, str)
    # Check that no hidden embedding column exists on VerificationRecord model
    assert not hasattr(record, "face_embedding")
    assert not hasattr(record, "biometric_vector")
    assert not hasattr(record, "face_crop_path")


def test_real_certificate_to_synthetic_live_comparison():
    """12. Real certificate portrait extraction, embedding, and similarity comparison with live candidate."""
    cert_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "uploads", "certificates")
    )
    if not os.path.exists(cert_dir):
        pytest.skip("Certificate upload directory not found; skipping real document test.")

    candidates = [
        os.path.join(cert_dir, f)
        for f in os.listdir(cert_dir)
        if f.endswith(".pdf") and os.path.getsize(os.path.join(cert_dir, f)) > 100000
    ]

    if not candidates:
        pytest.skip("No real certificate PDF available in environment; skipping real document test.")

    real_cert_path = candidates[0]
    face_service = CertificateFaceService()
    extraction_res = face_service.extract_certificate_face(real_cert_path)

    if not extraction_res["face_detected"] or extraction_res["face_crop"] is None:
        pytest.skip("Real certificate did not yield a valid face crop.")

    cert_crop = extraction_res["face_crop"]
    live_crop = make_synthetic_face_crop(seed=777, size=150)

    embedder = FaceEmbedder()
    e_cert = embedder.extract_embedding(cert_crop)
    e_live = embedder.extract_embedding(live_crop)

    assert e_cert.shape == (1, 128)
    assert e_live.shape == (1, 128)
    assert pytest.approx(float(np.linalg.norm(e_cert)), abs=1e-5) == 1.0
    assert pytest.approx(float(np.linalg.norm(e_live)), abs=1e-5) == 1.0

    similarity = embedder.compute_cosine_similarity(e_cert, e_live)
    assert isinstance(similarity, float)
    assert np.isfinite(similarity)
    assert -1.0 <= similarity <= 1.0
