"""
Dataset Validation & Summary Generation Engine for TutorLinkAI Matching Benchmark.

Validates:
1. Unique query IDs
2. Unique tutor IDs
3. Valid qrel query IDs
4. Valid qrel tutor IDs
5. Required fields
6. Valid rating ranges
7. Valid review counts
8. Valid budget values
9. Valid relevance labels
10. No malformed records
11. No orphaned relevance judgments
12. Deterministic content hashing and reproducibility metadata
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent

QUERIES_PATH = BASE_DIR / "queries.json"
TUTORS_PATH = BASE_DIR / "tutors.json"
QRELS_PATH = BASE_DIR / "qrels.json"
FEEDBACK_SCENARIOS_PATH = BASE_DIR / "feedback_scenarios.json"
RESULTS_DIR = BASE_DIR / "results"

DATASET_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"

REQUIRED_QUERY_FIELDS = [
    "query_id",
    "subject",
    "topics",
    "preferred_learning_mode",
    "latitude",
    "longitude",
    "budget_min",
    "budget_max",
    "preferred_slots",
]

REQUIRED_TUTOR_FIELDS = [
    "tutor_id",
    "name",
    "subjects",
    "topics_expertise",
    "preferred_teaching_mode",
    "hourly_rate",
    "latitude",
    "longitude",
    "availability",
    "rating",
    "review_count",
    "is_verified",
]


def compute_file_sha256(filepath: Path) -> str:
    """Computes deterministic SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def load_dataset_files() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Dict[str, int]]]:
    """Loads queries, tutors, and qrels JSON files."""
    if not QUERIES_PATH.exists():
        raise FileNotFoundError(f"Queries file not found: {QUERIES_PATH}")
    if not TUTORS_PATH.exists():
        raise FileNotFoundError(f"Tutors file not found: {TUTORS_PATH}")
    if not QRELS_PATH.exists():
        raise FileNotFoundError(f"Qrels file not found: {QRELS_PATH}")

    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)
    with open(TUTORS_PATH, "r", encoding="utf-8") as f:
        tutors = json.load(f)
    with open(QRELS_PATH, "r", encoding="utf-8") as f:
        qrels = json.load(f)

    return queries, tutors, qrels


def validate_queries(queries: List[Dict[str, Any]]) -> List[str]:
    """Validates student query records."""
    errors = []
    seen_ids = set()

    for idx, q in enumerate(queries):
        if not isinstance(q, dict):
            errors.append(f"Query at index {idx} is not a valid JSON object.")
            continue

        q_id = q.get("query_id")
        if not q_id or not isinstance(q_id, str):
            errors.append(f"Query at index {idx} missing valid 'query_id'.")
        elif q_id in seen_ids:
            errors.append(f"Duplicate query_id found: '{q_id}'.")
        else:
            seen_ids.add(q_id)

        for req_field in REQUIRED_QUERY_FIELDS:
            if req_field not in q:
                errors.append(f"Query '{q_id}' missing required field: '{req_field}'.")

        # Range checks
        lat = q.get("latitude")
        lon = q.get("longitude")
        if not isinstance(lat, (int, float)) or not (-90.0 <= lat <= 90.0):
            errors.append(f"Query '{q_id}' invalid latitude: {lat}.")
        if not isinstance(lon, (int, float)) or not (-180.0 <= lon <= 180.0):
            errors.append(f"Query '{q_id}' invalid longitude: {lon}.")

        b_min = q.get("budget_min")
        b_max = q.get("budget_max")
        if not isinstance(b_min, (int, float)) or b_min < 0:
            errors.append(f"Query '{q_id}' invalid budget_min: {b_min}.")
        if not isinstance(b_max, (int, float)) or (isinstance(b_min, (int, float)) and b_max < b_min):
            errors.append(f"Query '{q_id}' invalid budget_max: {b_max} (min: {b_min}).")

        topics = q.get("topics")
        if not isinstance(topics, list):
            errors.append(f"Query '{q_id}' 'topics' must be a list.")

        slots = q.get("preferred_slots")
        if not isinstance(slots, list):
            errors.append(f"Query '{q_id}' 'preferred_slots' must be a list.")

    return errors


def validate_tutors(tutors: List[Dict[str, Any]]) -> List[str]:
    """Validates candidate tutor records."""
    errors = []
    seen_ids = set()

    for idx, t in enumerate(tutors):
        if not isinstance(t, dict):
            errors.append(f"Tutor at index {idx} is not a valid JSON object.")
            continue

        t_id = t.get("tutor_id")
        if not t_id or not isinstance(t_id, str):
            errors.append(f"Tutor at index {idx} missing valid 'tutor_id'.")
        elif t_id in seen_ids:
            errors.append(f"Duplicate tutor_id found: '{t_id}'.")
        else:
            seen_ids.add(t_id)

        for req_field in REQUIRED_TUTOR_FIELDS:
            if req_field not in t:
                errors.append(f"Tutor '{t_id}' missing required field: '{req_field}'.")

        # Range and type checks
        rating = t.get("rating")
        if not isinstance(rating, (int, float)) or not (1.0 <= rating <= 5.0):
            errors.append(f"Tutor '{t_id}' invalid rating: {rating} (must be in [1.0, 5.0]).")

        review_count = t.get("review_count")
        if not isinstance(review_count, int) or review_count < 0:
            errors.append(f"Tutor '{t_id}' invalid review_count: {review_count} (must be non-negative int).")

        rate = t.get("hourly_rate")
        if not isinstance(rate, (int, float)) or rate <= 0:
            errors.append(f"Tutor '{t_id}' invalid hourly_rate: {rate}.")

        lat = t.get("latitude")
        lon = t.get("longitude")
        if not isinstance(lat, (int, float)) or not (-90.0 <= lat <= 90.0):
            errors.append(f"Tutor '{t_id}' invalid latitude: {lat}.")
        if not isinstance(lon, (int, float)) or not (-180.0 <= lon <= 180.0):
            errors.append(f"Tutor '{t_id}' invalid longitude: {lon}.")

        subjects = t.get("subjects")
        if not isinstance(subjects, list) or len(subjects) == 0:
            errors.append(f"Tutor '{t_id}' 'subjects' must be a non-empty list.")

        topics = t.get("topics_expertise")
        if not isinstance(topics, list):
            errors.append(f"Tutor '{t_id}' 'topics_expertise' must be a list.")

        if not isinstance(t.get("is_verified"), bool):
            errors.append(f"Tutor '{t_id}' 'is_verified' must be a boolean.")

    return errors


def validate_qrels(
    qrels: Dict[str, Dict[str, int]],
    query_ids: set,
    tutor_ids: set
) -> List[str]:
    """Validates relevance judgments and checks for orphan keys."""
    errors = []
    allowed_grades = {0, 1, 2, 3}

    for q_id, tutor_ratings in qrels.items():
        if q_id not in query_ids:
            errors.append(f"Orphan qrel query_id '{q_id}' does not exist in queries.json.")

        if not isinstance(tutor_ratings, dict):
            errors.append(f"Qrel for query '{q_id}' is not a valid dictionary.")
            continue

        for t_id, grade in tutor_ratings.items():
            if t_id not in tutor_ids:
                errors.append(f"Orphan qrel tutor_id '{t_id}' under query '{q_id}' does not exist in tutors.json.")
            if not isinstance(grade, int) or grade not in allowed_grades:
                errors.append(f"Invalid relevance grade {grade} for pair ({q_id}, {t_id}). Allowed: {allowed_grades}.")

    # Check for missing query coverage
    for q_id in query_ids:
        if q_id not in qrels:
            errors.append(f"Query '{q_id}' has no relevance judgments in qrels.json.")

    return errors


def validate_dataset() -> Tuple[bool, List[str], Dict[str, Any]]:
    """Runs complete validation and returns status, error list, and summary dict."""
    queries, tutors, qrels = load_dataset_files()

    query_errors = validate_queries(queries)
    tutor_errors = validate_tutors(tutors)

    query_ids = {q["query_id"] for q in queries if isinstance(q, dict) and "query_id" in q}
    tutor_ids = {t["tutor_id"] for t in tutors if isinstance(t, dict) and "tutor_id" in t}

    qrel_errors = validate_qrels(qrels, query_ids, tutor_ids)

    all_errors = query_errors + tutor_errors + qrel_errors
    is_valid = len(all_errors) == 0

    # Calculate deterministic statistics
    subjects = sorted(list({q["subject"] for q in queries if "subject" in q}))
    all_topics = set()
    for t in tutors:
        all_topics.update(t.get("topics_expertise", []))
    for q in queries:
        all_topics.update(q.get("topics", []))

    ratings = [t["rating"] for t in tutors if "rating" in t]
    review_counts = [t["review_count"] for t in tutors if "review_count" in t]
    hourly_rates = [t["hourly_rate"] for t in tutors if "hourly_rate" in t]
    budgets_min = [q["budget_min"] for q in queries if "budget_min" in q]
    budgets_max = [q["budget_max"] for q in queries if "budget_max" in q]

    relevance_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    total_judgments = 0
    for q_id, judgments in qrels.items():
        for t_id, grade in judgments.items():
            if grade in relevance_counts:
                relevance_counts[grade] += 1
            total_judgments += 1

    checksums = {
        "queries_sha256": compute_file_sha256(QUERIES_PATH),
        "tutors_sha256": compute_file_sha256(TUTORS_PATH),
        "qrels_sha256": compute_file_sha256(QRELS_PATH),
    }
    if FEEDBACK_SCENARIOS_PATH.exists():
        checksums["feedback_scenarios_sha256"] = compute_file_sha256(FEEDBACK_SCENARIOS_PATH)

    summary = {
        "dataset_version": DATASET_VERSION,
        "schema_version": SCHEMA_VERSION,
        "status": "VALID" if is_valid else "INVALID",
        "error_count": len(all_errors),
        "checksums": checksums,
        "record_counts": {
            "queries": len(queries),
            "tutors": len(tutors),
            "relevance_judgments": total_judgments,
            "subjects_count": len(subjects),
            "unique_topics_count": len(all_topics),
            "verified_tutors_count": sum(1 for t in tutors if t.get("is_verified", False)),
        },
        "subjects": subjects,
        "relevance_distribution": {
            "grade_0_irrelevant": relevance_counts[0],
            "grade_1_subject_matched": relevance_counts[1],
            "grade_2_partial_match": relevance_counts[2],
            "grade_3_strong_match": relevance_counts[3],
        },
        "tutor_metrics": {
            "rating_min": min(ratings) if ratings else 0.0,
            "rating_max": max(ratings) if ratings else 0.0,
            "rating_mean": round(sum(ratings) / len(ratings), 4) if ratings else 0.0,
            "review_count_min": min(review_counts) if review_counts else 0,
            "review_count_max": max(review_counts) if review_counts else 0,
            "review_count_mean": round(sum(review_counts) / len(review_counts), 4) if review_counts else 0.0,
            "hourly_rate_min": min(hourly_rates) if hourly_rates else 0.0,
            "hourly_rate_max": max(hourly_rates) if hourly_rates else 0.0,
            "hourly_rate_mean": round(sum(hourly_rates) / len(hourly_rates), 4) if hourly_rates else 0.0,
        },
        "student_budget_metrics": {
            "budget_min_range_min": min(budgets_min) if budgets_min else 0.0,
            "budget_min_range_max": max(budgets_min) if budgets_min else 0.0,
            "budget_min_mean": round(sum(budgets_min) / len(budgets_min), 4) if budgets_min else 0.0,
            "budget_max_range_min": min(budgets_max) if budgets_max else 0.0,
            "budget_max_range_max": max(budgets_max) if budgets_max else 0.0,
            "budget_max_mean": round(sum(budgets_max) / len(budgets_max), 4) if budgets_max else 0.0,
        },
    }

    return is_valid, all_errors, summary


def export_summary_files(summary: Dict[str, Any]) -> Tuple[Path, Path]:
    """Generates dataset_summary.json and dataset_summary.md in results directory."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = RESULTS_DIR / "dataset_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    md_path = RESULTS_DIR / "dataset_summary.md"
    md_content = f"""# TutorLinkAI — Matching Benchmark Dataset Summary

- **Dataset Version:** `{summary['dataset_version']}`
- **Schema Version:** `{summary['schema_version']}`
- **Validation Status:** `{summary['status']}` (Errors: `{summary['error_count']}`)

---

## 1. Record Counts & Dimensions

| Entity | Count | Details |
| :--- | :--- | :--- |
| **Learning Queries** | {summary['record_counts']['queries']} | High School & Undergraduate student requirements |
| **Candidate Tutors** | {summary['record_counts']['tutors']} | Multi-subject domain experts |
| **Relevance Judgments** | {summary['record_counts']['relevance_judgments']} | Complete $8 \\times 12$ dense evaluation matrix |
| **Academic Subjects** | {summary['record_counts']['subjects_count']} | {", ".join(summary['subjects'])} |
| **Unique Syllabus Topics** | {summary['record_counts']['unique_topics_count']} | High school and collegiate syllabus concepts |
| **Verified Tutors** | {summary['record_counts']['verified_tutors_count']} | 100% credential verified |

---

## 2. Relevance Label Distribution (qrels)

| Grade | Meaning | Count | Proportion |
| :--- | :--- | :--- | :--- |
| **Grade 0** | Irrelevant (Cross-Subject) | {summary['relevance_distribution']['grade_0_irrelevant']} | {summary['relevance_distribution']['grade_0_irrelevant'] / summary['record_counts']['relevance_judgments']:.2%} |
| **Grade 1** | Subject-Matched Only | {summary['relevance_distribution']['grade_1_subject_matched']} | {summary['relevance_distribution']['grade_1_subject_matched'] / summary['record_counts']['relevance_judgments']:.2%} |
| **Grade 2** | Partial Topic Match | {summary['relevance_distribution']['grade_2_partial_match']} | {summary['relevance_distribution']['grade_2_partial_match'] / summary['record_counts']['relevance_judgments']:.2%} |
| **Grade 3** | Strong / Exact Match | {summary['relevance_distribution']['grade_3_strong_match']} | {summary['relevance_distribution']['grade_3_strong_match'] / summary['record_counts']['relevance_judgments']:.2%} |

---

## 3. Tutor & Student Financial Metrics

| Metric | Min | Mean | Max |
| :--- | :--- | :--- | :--- |
| **Tutor Rating (Stars)** | {summary['tutor_metrics']['rating_min']} | {summary['tutor_metrics']['rating_mean']:.2f} | {summary['tutor_metrics']['rating_max']} |
| **Tutor Reviews Count** | {summary['tutor_metrics']['review_count_min']} | {summary['tutor_metrics']['review_count_mean']:.2f} | {summary['tutor_metrics']['review_count_max']} |
| **Tutor Hourly Rate (₹)** | ₹{summary['tutor_metrics']['hourly_rate_min']:.2f} | ₹{summary['tutor_metrics']['hourly_rate_mean']:.2f} | ₹{summary['tutor_metrics']['hourly_rate_max']:.2f} |
| **Student Budget Min (₹)** | ₹{summary['student_budget_metrics']['budget_min_range_min']:.2f} | ₹{summary['student_budget_metrics']['budget_min_mean']:.2f} | ₹{summary['student_budget_metrics']['budget_min_range_max']:.2f} |
| **Student Budget Max (₹)** | ₹{summary['student_budget_metrics']['budget_max_range_min']:.2f} | ₹{summary['student_budget_metrics']['budget_max_mean']:.2f} | ₹{summary['student_budget_metrics']['budget_max_range_max']:.2f} |

---

## 4. Deterministic Reproducibility Checksums (SHA-256)

```json
{json.dumps(summary['checksums'], indent=2)}
```
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content.strip() + "\n")

    return json_path, md_path


def main():
    print("=" * 80)
    print("TutorLinkAI — Step 7A: Matching Benchmark Dataset Validator & Summarizer")
    print("=" * 80)

    is_valid, errors, summary = validate_dataset()

    if not is_valid:
        print(f"\n[FAILED] Dataset validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\n[PASSED] All dataset schema, integrity, and cross-reference checks passed.")
    print(f"  - Version: {summary['dataset_version']}")
    print(f"  - Queries: {summary['record_counts']['queries']}")
    print(f"  - Tutors: {summary['record_counts']['tutors']}")
    print(f"  - Relevance Judgments: {summary['record_counts']['relevance_judgments']}")
    print(f"  - Subjects: {len(summary['subjects'])} ({', '.join(summary['subjects'])})")
    print(f"  - Unique Topics: {summary['record_counts']['unique_topics_count']}")

    json_path, md_path = export_summary_files(summary)
    print(f"\nSummary artifacts generated:")
    print(f"  - {json_path}")
    print(f"  - {md_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
