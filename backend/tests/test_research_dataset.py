import sys
import json
from pathlib import Path
import pytest

# Ensure repo root and ai-service are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AI_SERVICE_DIR = BASE_DIR / "ai-service"
if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from evaluation.matching.validate_dataset import (
    validate_dataset,
    load_dataset_files,
    compute_file_sha256,
    QUERIES_PATH,
    TUTORS_PATH,
    QRELS_PATH,
    FEEDBACK_SCENARIOS_PATH,
    REQUIRED_QUERY_FIELDS,
    REQUIRED_TUTOR_FIELDS,
)
from app.matching.config import (
    DEFAULT_WEIGHT_LEARNING_NEED,
    DEFAULT_WEIGHT_LOCATION,
    DEFAULT_WEIGHT_FEE,
    DEFAULT_WEIGHT_TIME,
)


def test_dataset_files_exist():
    assert QUERIES_PATH.exists(), f"Missing {QUERIES_PATH}"
    assert TUTORS_PATH.exists(), f"Missing {TUTORS_PATH}"
    assert QRELS_PATH.exists(), f"Missing {QRELS_PATH}"
    assert FEEDBACK_SCENARIOS_PATH.exists(), f"Missing {FEEDBACK_SCENARIOS_PATH}"


def test_dataset_json_parses():
    queries, tutors, qrels = load_dataset_files()
    assert isinstance(queries, list)
    assert isinstance(tutors, list)
    assert isinstance(qrels, dict)
    assert len(queries) == 8
    assert len(tutors) == 12


def test_ids_are_unique():
    queries, tutors, _ = load_dataset_files()

    query_ids = [q["query_id"] for q in queries]
    assert len(query_ids) == len(set(query_ids)), "Duplicate query IDs found"

    tutor_ids = [t["tutor_id"] for t in tutors]
    assert len(tutor_ids) == len(set(tutor_ids)), "Duplicate tutor IDs found"


def test_qrels_reference_valid_records():
    queries, tutors, qrels = load_dataset_files()
    query_id_set = {q["query_id"] for q in queries}
    tutor_id_set = {t["tutor_id"] for t in tutors}

    for q_id, tutor_grades in qrels.items():
        assert q_id in query_id_set, f"qrel query_id '{q_id}' not in queries.json"
        for t_id in tutor_grades.keys():
            assert t_id in tutor_id_set, f"qrel tutor_id '{t_id}' under '{q_id}' not in tutors.json"


def test_required_fields_exist():
    queries, tutors, _ = load_dataset_files()

    for q in queries:
        for field in REQUIRED_QUERY_FIELDS:
            assert field in q, f"Query '{q.get('query_id')}' missing required field '{field}'"

    for t in tutors:
        for field in REQUIRED_TUTOR_FIELDS:
            assert field in t, f"Tutor '{t.get('tutor_id')}' missing required field '{field}'"


def test_ratings_are_valid():
    _, tutors, _ = load_dataset_files()
    for t in tutors:
        rating = t.get("rating")
        assert isinstance(rating, (int, float)), f"Tutor '{t['tutor_id']}' rating not numeric"
        assert 1.0 <= rating <= 5.0, f"Tutor '{t['tutor_id']}' rating {rating} outside [1.0, 5.0]"


def test_review_counts_are_valid():
    _, tutors, _ = load_dataset_files()
    for t in tutors:
        rev_count = t.get("review_count")
        assert isinstance(rev_count, int), f"Tutor '{t['tutor_id']}' review_count not int"
        assert rev_count >= 0, f"Tutor '{t['tutor_id']}' review_count {rev_count} is negative"


def test_relevance_labels_are_valid():
    _, _, qrels = load_dataset_files()
    allowed_grades = {0, 1, 2, 3}
    for q_id, tutor_grades in qrels.items():
        for t_id, grade in tutor_grades.items():
            assert isinstance(grade, int), f"Grade for ({q_id}, {t_id}) is not int"
            assert grade in allowed_grades, f"Grade {grade} for ({q_id}, {t_id}) not in {allowed_grades}"


def test_dataset_summary_is_reproducible():
    is_valid, errors, summary = validate_dataset()
    assert is_valid is True
    assert len(errors) == 0

    assert summary["dataset_version"] == "1.0.0"
    assert summary["record_counts"]["queries"] == 8
    assert summary["record_counts"]["tutors"] == 12
    assert summary["record_counts"]["relevance_judgments"] == 96
    assert summary["record_counts"]["verified_tutors_count"] == 12
    assert summary["relevance_distribution"]["grade_3_strong_match"] == 8
    assert summary["relevance_distribution"]["grade_0_irrelevant"] == 78


def test_validator_produces_deterministic_output():
    is_valid1, errors1, summary1 = validate_dataset()
    is_valid2, errors2, summary2 = validate_dataset()

    assert is_valid1 == is_valid2 == True
    assert errors1 == errors2 == []
    assert summary1 == summary2


def test_content_checksums_are_deterministic():
    hash1 = compute_file_sha256(QUERIES_PATH)
    hash2 = compute_file_sha256(QUERIES_PATH)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_production_matching_weights_remain_unmodified():
    # Verify strict isolation from production weights
    assert DEFAULT_WEIGHT_LEARNING_NEED == 0.45
    assert DEFAULT_WEIGHT_LOCATION == 0.20
    assert DEFAULT_WEIGHT_FEE == 0.20
    assert DEFAULT_WEIGHT_TIME == 0.15
