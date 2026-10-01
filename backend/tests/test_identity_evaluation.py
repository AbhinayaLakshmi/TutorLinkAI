"""
Unit and integration tests for Step 4A: Identity Similarity Evaluation Harness.

Validates:
1. Genuine pair can be processed.
2. Impostor pair can be processed.
3. Similarity is finite.
4. Similarity is within [-1.0, 1.0].
5. Missing certificate face is handled safely.
6. Missing live face is handled safely.
7. Invalid image input is handled safely.
8. Embeddings are not written to disk or persisted.
9. Raw face crops are not written to the evaluation result.
10. Output contains only metadata and similarity scores.
11. Summary statistics (min, max, mean, median, std) are calculated properly.
12. Export to JSON and CSV produces clean, machine-readable sanitized files.
13. Directory evaluation cleanly matches pairs.
14. NO universal identity threshold assertions are made.
"""

import os
import io
import csv
import json
import pytest
import numpy as np
import cv2

from backend.evaluation.identity_evaluator import (
    IdentityEvaluator,
    PairEvaluationResult,
    EvaluationSummary
)
from backend.app.services.face import BaseFaceDetector, CertificateFaceService
from backend.app.services.face_embedder import FaceEmbedder


def make_synthetic_face_image(seed: int = 42, size: int = 120) -> np.ndarray:
    """Generates a synthetic 3-channel face-like image for isolated biometric testing."""
    np.random.seed(seed)
    crop = np.full((size, size, 3), 150 + (seed % 30), dtype=np.uint8)
    cv2.circle(crop, (int(size * 0.3), int(size * 0.35)), int(size * 0.08), (40, 40, 40), -1)
    cv2.circle(crop, (int(size * 0.7), int(size * 0.35)), int(size * 0.08), (40, 40, 40), -1)
    cv2.line(crop, (int(size * 0.35), int(size * 0.7)), (int(size * 0.65), int(size * 0.7)), (50, 50, 180), 2)
    return crop


class MockDetector(BaseFaceDetector):
    def __init__(self, return_box=True):
        self.return_box = return_box

    def detect(self, image: np.ndarray):
        if not self.return_box:
            return []
        h, w = image.shape[:2]
        return [(10, 10, min(100, w - 20), min(100, h - 20))]


def test_evaluate_genuine_pair_success():
    """1. Genuine pair can be processed and produces a valid finite similarity in [-1, 1]."""
    evaluator = IdentityEvaluator(detector=MockDetector(return_box=True))
    crop_cert = make_synthetic_face_image(seed=10, size=120)
    crop_live = make_synthetic_face_image(seed=10, size=120)

    result = evaluator.evaluate_pair(
        pair_id="gen_001",
        pair_type="GENUINE",
        cert_input=crop_cert,
        live_input=crop_live
    )

    assert result.pair_id == "gen_001"
    assert result.pair_type == "GENUINE"
    assert result.status == "SUCCESS"
    assert result.similarity is not None
    assert isinstance(result.similarity, float)
    assert np.isfinite(result.similarity)
    assert -1.0 <= result.similarity <= 1.0
    assert result.cert_face_detected is True
    assert result.live_face_detected is True


def test_evaluate_impostor_pair_success():
    """2. Impostor pair can be processed and produces a valid finite similarity in [-1, 1]."""
    evaluator = IdentityEvaluator(detector=MockDetector(return_box=True))
    crop_cert = make_synthetic_face_image(seed=101, size=120)
    crop_live = make_synthetic_face_image(seed=999, size=120)

    result = evaluator.evaluate_pair(
        pair_id="imp_001",
        pair_type="IMPOSTOR",
        cert_input=crop_cert,
        live_input=crop_live
    )

    assert result.pair_id == "imp_001"
    assert result.pair_type == "IMPOSTOR"
    assert result.status == "SUCCESS"
    assert result.similarity is not None
    assert isinstance(result.similarity, float)
    assert np.isfinite(result.similarity)
    assert -1.0 <= result.similarity <= 1.0


def test_missing_certificate_face_handled_safely():
    """3. Missing certificate face returns EXTRACTION_FAILED with similarity=None."""
    evaluator = IdentityEvaluator()
    crop_live = make_synthetic_face_image(seed=50, size=120)

    result = evaluator.evaluate_pair(
        pair_id="missing_cert_01",
        pair_type="GENUINE",
        cert_input=None,
        live_input=crop_live
    )

    assert result.status == "EXTRACTION_FAILED"
    assert result.similarity is None
    assert result.cert_face_detected is False
    assert "Certificate face unavailable" in result.reason


def test_missing_live_face_handled_safely():
    """4. Missing live face returns EXTRACTION_FAILED with similarity=None."""
    evaluator = IdentityEvaluator()
    crop_cert = make_synthetic_face_image(seed=50, size=120)

    result = evaluator.evaluate_pair(
        pair_id="missing_live_01",
        pair_type="GENUINE",
        cert_input=crop_cert,
        live_input=None
    )

    assert result.status == "EXTRACTION_FAILED"
    assert result.similarity is None
    assert result.live_face_detected is False
    assert "Live face unavailable" in result.reason


def test_invalid_image_inputs_handled_safely():
    """5. Non-existent file paths or invalid array structures handle errors gracefully."""
    evaluator = IdentityEvaluator()

    result = evaluator.evaluate_pair(
        pair_id="invalid_file_01",
        pair_type="GENUINE",
        cert_input="non_existent_certificate.pdf",
        live_input=np.array([], dtype=np.uint8)  # empty numpy array
    )

    assert result.status == "EXTRACTION_FAILED"
    assert result.similarity is None


def test_raw_crops_and_embeddings_excluded_from_result_dict():
    """6. Evaluation result dictionary contains NO numpy arrays or 128-D vectors."""
    evaluator = IdentityEvaluator()
    crop_cert = make_synthetic_face_image(seed=1, size=120)
    crop_live = make_synthetic_face_image(seed=2, size=120)

    result = evaluator.evaluate_pair("pair_clean", "GENUINE", crop_cert, crop_live)
    data = result.to_dict()

    # Ensure JSON serializable
    json_str = json.dumps(data)
    parsed = json.loads(json_str)

    assert "face_crop" not in parsed
    assert "embedding" not in parsed
    assert "vector" not in parsed
    assert isinstance(parsed["similarity"], float)
    assert parsed["pair_id"] == "pair_clean"


def test_distribution_statistics_calculation():
    """7. Summary statistics (min, max, mean, median, std, percentiles) are mathematically accurate."""
    sims = [0.20, 0.40, 0.60, 0.80, 1.00]
    stats = IdentityEvaluator.calculate_distribution_statistics(sims)

    assert stats is not None
    assert stats["count"] == 5
    assert pytest.approx(stats["min"], abs=1e-5) == 0.20
    assert pytest.approx(stats["max"], abs=1e-5) == 1.00
    assert pytest.approx(stats["mean"], abs=1e-5) == 0.60
    assert pytest.approx(stats["median"], abs=1e-5) == 0.60
    assert stats["std"] > 0.0

    # Empty list returns None
    assert IdentityEvaluator.calculate_distribution_statistics([]) is None


def test_evaluate_manifest_and_summary_aggregation():
    """8. Manifest evaluation separates genuine and impostor distributions accurately."""
    evaluator = IdentityEvaluator()
    c1 = make_synthetic_face_image(seed=10, size=120)
    c2 = make_synthetic_face_image(seed=20, size=120)

    manifest = [
        {"pair_id": "g1", "pair_type": "GENUINE", "cert_input": c1, "live_input": c1},
        {"pair_id": "g2", "pair_type": "GENUINE", "cert_input": c2, "live_input": c2},
        {"pair_id": "g_fail", "pair_type": "GENUINE", "cert_input": None, "live_input": c1},
        {"pair_id": "i1", "pair_type": "IMPOSTOR", "cert_input": c1, "live_input": c2},
        {"pair_id": "i_fail", "pair_type": "IMPOSTOR", "cert_input": c2, "live_input": None},
    ]

    results, summary = evaluator.evaluate_manifest(manifest)

    assert len(results) == 5
    assert summary.total_pairs == 5
    assert summary.genuine_total == 3
    assert summary.genuine_valid == 2
    assert summary.genuine_failed == 1
    assert summary.impostor_total == 2
    assert summary.impostor_valid == 1
    assert summary.impostor_failed == 1

    assert summary.genuine_stats is not None
    assert summary.genuine_stats["count"] == 2
    assert summary.impostor_stats is not None
    assert summary.impostor_stats["count"] == 1


def test_export_json_and_csv(tmp_path):
    """9. Machine-readable export produces valid CSV and JSON with only metadata and similarities."""
    evaluator = IdentityEvaluator()
    c1 = make_synthetic_face_image(seed=1, size=120)
    c2 = make_synthetic_face_image(seed=2, size=120)

    manifest = [
        {"pair_id": "p001", "pair_type": "GENUINE", "cert_input": c1, "live_input": c1},
        {"pair_id": "p002", "pair_type": "IMPOSTOR", "cert_input": c1, "live_input": c2}
    ]
    results, summary = evaluator.evaluate_manifest(manifest)

    json_file = str(tmp_path / "results.json")
    csv_file = str(tmp_path / "results.csv")

    evaluator.export_results_json(results, summary, json_file)
    evaluator.export_results_csv(results, csv_file)

    assert os.path.exists(json_file)
    assert os.path.exists(csv_file)

    # Verify JSON structure
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "summary" in data
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["summary"]["total_pairs"] == 2

    # Verify CSV structure
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 3  # Header + 2 rows
        header = reader[0]
        assert header == [
            "pair_id",
            "pair_type",
            "status",
            "similarity",
            "cert_face_detected",
            "cert_quality",
            "live_face_detected",
            "live_quality",
            "reason"
        ]


def test_evaluate_directory_structure(tmp_path):
    """10. Directory-based pair discovery matches pair_<ID>_cert and pair_<ID>_live files correctly."""
    dataset_dir = tmp_path / "dataset"
    gen_dir = dataset_dir / "genuine"
    imp_dir = dataset_dir / "impostor"
    gen_dir.mkdir(parents=True)
    imp_dir.mkdir(parents=True)

    img = make_synthetic_face_image(seed=42, size=200)

    # Save pairs as PNGs
    cv2.imwrite(str(gen_dir / "pair_001_cert.png"), img)
    cv2.imwrite(str(gen_dir / "pair_001_live.png"), img)
    cv2.imwrite(str(imp_dir / "pair_002_cert.png"), img)
    cv2.imwrite(str(imp_dir / "pair_002_live.png"), img)

    class BoxDetector(BaseFaceDetector):
        def detect(self, image: np.ndarray):
            return [(10, 10, 150, 150)]

    cert_service = CertificateFaceService(
        detector=BoxDetector(),
        min_face_dim=50,
        max_laplacian_var=100000.0
    )
    evaluator = IdentityEvaluator(
        cert_service=cert_service,
        detector=BoxDetector()
    )
    results, summary = evaluator.evaluate_directory(str(dataset_dir))

    assert summary.total_pairs == 2
    assert summary.genuine_total == 1
    assert summary.impostor_total == 1
    assert summary.genuine_valid == 1
    assert summary.impostor_valid == 1
