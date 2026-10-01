import os
import pytest
import numpy as np
import cv2
from backend.app.services.face_embedder import FaceEmbedder, DEFAULT_MODEL_PATH
from backend.app.services.face import CertificateFaceService


def test_model_initialization():
    """1. Model initialization succeeds with the SFace model."""
    assert os.path.exists(DEFAULT_MODEL_PATH), f"Model weight file missing at {DEFAULT_MODEL_PATH}"
    embedder = FaceEmbedder()
    assert embedder is not None
    assert embedder.recognizer is not None


def test_embedding_output_properties():
    """2. A valid face image produces expected dtype, shape, and non-zero finite values."""
    embedder = FaceEmbedder()
    # Simulated 112x112 face crop (skin-tone image with features)
    dummy_crop = np.full((112, 112, 3), 150, dtype=np.uint8)
    cv2.circle(dummy_crop, (35, 40), 10, (50, 50, 50), -1)  # Left eye
    cv2.circle(dummy_crop, (75, 40), 10, (50, 50, 50), -1)  # Right eye
    cv2.line(dummy_crop, (40, 85), (72, 85), (60, 60, 180), 3)  # Mouth

    emb = embedder.extract_embedding(dummy_crop)

    assert isinstance(emb, np.ndarray)
    assert emb.dtype == np.float32
    assert emb.shape == (1, 128)
    assert np.all(np.isfinite(emb))
    assert np.linalg.norm(emb) > 0.0


def test_l2_normalization():
    """3. Verify the returned embedding L2 norm is approximately 1.0."""
    embedder = FaceEmbedder()
    dummy_crop = np.random.randint(50, 200, (140, 140, 3), dtype=np.uint8)

    emb = embedder.extract_embedding(dummy_crop)
    norm = float(np.linalg.norm(emb))

    assert pytest.approx(norm, abs=1e-5) == 1.0


def test_identical_input_self_similarity():
    """4. Embedding compared with itself produces cosine similarity approximately 1.0."""
    embedder = FaceEmbedder()
    dummy_crop = np.full((120, 120, 3), 160, dtype=np.uint8)
    cv2.circle(dummy_crop, (40, 40), 8, (30, 30, 30), -1)
    cv2.circle(dummy_crop, (80, 40), 8, (30, 30, 30), -1)

    emb = embedder.extract_embedding(dummy_crop)
    sim = embedder.compute_cosine_similarity(emb, emb)

    assert isinstance(sim, float)
    assert pytest.approx(sim, abs=1e-5) == 1.0


def test_embedding_determinism():
    """5. Running embedding extraction twice on the same image produces identical vectors."""
    embedder = FaceEmbedder()
    dummy_crop = np.random.randint(0, 255, (130, 130, 3), dtype=np.uint8)

    emb1 = embedder.extract_embedding(dummy_crop)
    emb2 = embedder.extract_embedding(dummy_crop)

    assert np.allclose(emb1, emb2, atol=1e-6)


def test_invalid_input_rejections():
    """6. Invalid inputs (None, empty, wrong channels/dimensions) fail cleanly with ValueError."""
    embedder = FaceEmbedder()

    # None input
    with pytest.raises(ValueError, match="cannot be None"):
        embedder.extract_embedding(None)

    # Empty array
    with pytest.raises(ValueError, match="empty"):
        embedder.extract_embedding(np.array([], dtype=np.uint8))

    # 2D grayscale (missing channel dimension)
    with pytest.raises(ValueError, match="must have 3 dimensions"):
        embedder.extract_embedding(np.zeros((112, 112), dtype=np.uint8))

    # Single-channel 3D array (112, 112, 1)
    with pytest.raises(ValueError, match="must have 3 color channels"):
        embedder.extract_embedding(np.zeros((112, 112, 1), dtype=np.uint8))

    # 4-channel BGRA array (112, 112, 4)
    with pytest.raises(ValueError, match="must have 3 color channels"):
        embedder.extract_embedding(np.zeros((112, 112, 4), dtype=np.uint8))

    # Resolution too small
    with pytest.raises(ValueError, match="too small"):
        embedder.extract_embedding(np.zeros((10, 10, 3), dtype=np.uint8))

    # Invalid similarity inputs
    valid_emb = np.zeros((1, 128), dtype=np.float32)
    valid_emb[0, 0] = 1.0

    with pytest.raises(ValueError, match="cannot be None"):
        embedder.compute_cosine_similarity(None, valid_emb)

    with pytest.raises(ValueError, match="shape mismatch"):
        embedder.compute_cosine_similarity(valid_emb, np.zeros((1, 64), dtype=np.float32))


def test_real_certificate_crop_embedding():
    """7. Extract and embed face from real certificate if present in the environment."""
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

    face_crop = extraction_res["face_crop"]
    assert isinstance(face_crop, np.ndarray)
    assert len(face_crop.shape) == 3

    embedder = FaceEmbedder()
    embedding = embedder.extract_embedding(face_crop)

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1, 128)
    assert embedding.dtype == np.float32
    assert pytest.approx(float(np.linalg.norm(embedding)), abs=1e-5) == 1.0

    # Test self-similarity of real portrait
    self_sim = embedder.compute_cosine_similarity(embedding, embedding)
    assert pytest.approx(self_sim, abs=1e-5) == 1.0
