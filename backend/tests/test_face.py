import pytest
import os
import numpy as np
import cv2
from backend.app.services.face import CertificateFaceService, HaarCascadeFaceDetector, BaseFaceDetector

# Real certificate path for local validation in tests
REAL_CERT_PATH = "/Users/awinthika/Desktop/TutorLinkAI/backend/uploads/certificates/68efe53a-a0c7-44c6-b4ec-90f7de38f16c.pdf"

class MockFaceDetector(BaseFaceDetector):
    """
    Mock detector for controlling returns in unit testing.
    """
    def __init__(self, mock_boxes=None):
        self.mock_boxes = mock_boxes or []
        
    def detect(self, image: np.ndarray):
        return self.mock_boxes


def test_pdf_rendering():
    if not os.path.exists(REAL_CERT_PATH):
        pytest.skip("Real certificate not found in environment; skipping rendering test.")
        
    service = CertificateFaceService()
    img = service.render_pdf_page(REAL_CERT_PATH, page_idx=0, scale=4)
    
    assert isinstance(img, np.ndarray)
    assert len(img.shape) == 3  # BGR channel format
    assert img.shape[0] > 0
    assert img.shape[1] > 0


def test_emblem_rejection():
    service = CertificateFaceService()
    
    # 1. Simulate a high-contrast line-art stamp (e.g. alternating black/white bands)
    logo_img = np.zeros((150, 150, 3), dtype=np.uint8)
    for i in range(0, 150, 10):
        logo_img[i:i+5, :, :] = 255  # High-frequency horizontal lines
        
    is_seal, reason, score = service._is_emblem_or_seal(logo_img)
    assert is_seal is True
    assert "High texture variance" in reason
    
    # 2. Simulate a smooth gradient patch (resembling skin regions/faces)
    face_stub = np.zeros((150, 150, 3), dtype=np.uint8)
    cv2.GaussianBlur(face_stub, (25, 25), 0, face_stub)
    is_seal, reason, score = service._is_emblem_or_seal(face_stub)
    assert is_seal is False


def test_face_quality_assessment():
    service = CertificateFaceService()
    
    # Large enough, high-contrast face
    crop = np.random.randint(0, 255, (120, 120, 3), dtype=np.uint8)
    bbox = (0, 0, 120, 120)
    info = service.analyze_face_quality(crop, bbox)
    
    assert info["quality"] == "GOOD"
    assert info["suitable_for_matching"] is True
    assert info["face_width"] == 120
    assert info["face_height"] == 120
    
    # Small face crop (not suitable for embedding models)
    small_crop = np.random.randint(0, 255, (80, 80, 3), dtype=np.uint8)
    small_bbox = (0, 0, 80, 80)
    small_info = service.analyze_face_quality(small_crop, small_bbox)
    
    assert small_info["quality"] == "POOR"
    assert small_info["suitable_for_matching"] is False


def test_no_face_case():
    temp_path = "temp_mock_cert.png"
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    cv2.imwrite(temp_path, img)
    
    try:
        # Set up service with mock detector returning no faces
        service = CertificateFaceService(detector=MockFaceDetector([]))
        res = service.process_certificate(temp_path)
        
        assert res["face_detected"] is False
        assert res["face_count"] == 0
        assert res["quality"] == "NOT_AVAILABLE"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_multiple_faces_case():
    temp_path = "temp_mock_cert_multi.png"
    img = np.zeros((600, 600, 3), dtype=np.uint8)
    cv2.imwrite(temp_path, img)
    
    try:
        # Two valid large faces with low-frequency variance
        service = CertificateFaceService(
            detector=MockFaceDetector([
                (50, 50, 150, 150),
                (250, 250, 150, 150)
            ]),
            max_laplacian_var=100.0,
            min_face_dim=100
        )
        
        res = service.process_certificate(temp_path)
        
        assert res["face_detected"] is True
        assert res["face_count"] == 2
        assert res["quality"] == "REQUIRES_REVIEW"
        assert "candidates" in res
        assert len(res["candidates"]) == 2
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_real_ashwin_certificate_e2e():
    if not os.path.exists(REAL_CERT_PATH):
        pytest.skip("Real certificate not found; skipping E2E face validation.")
        
    service = CertificateFaceService()
    res = service.process_certificate(REAL_CERT_PATH)
    
    # Validate expected results for S. Ashwin's certificate
    assert res["face_detected"] is True
    assert res["face_count"] == 1
    assert res["source_page"] == 0
    
    # Bounding Box should align with the student's portrait on Page 0
    # Expected bbox is [1611, 969, 144, 144]
    bbox = res["bounding_box"]
    assert bbox[0] > 1500
    assert bbox[1] > 900
    assert 130 <= res["face_width"] <= 160
    assert 130 <= res["face_height"] <= 160
    assert res["quality"] == "GOOD"
    assert res["suitable_for_matching"] is True
    assert "emblem" not in res["reason"]
