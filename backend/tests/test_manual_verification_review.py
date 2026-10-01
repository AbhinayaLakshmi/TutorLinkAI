import os
import pytest
from datetime import datetime
from fastapi import status

from backend.app.core.security import create_access_token
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.tutor import TutorProfile, Education, TutorExpertise, Certificate
from backend.app.models.verification import VerificationRecord, VerificationReview


def _create_user_with_token(db, email, role, full_name):
    user = User(
        email=email,
        hashed_password="hashedpassword123!",
        full_name=full_name,
        phone_number="9876543210",
        role=role,
        email_verified=True,
        onboarding_status="COMPLETED",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def _setup_test_tutor(db, email="tutor_eval@example.com", name="Candidate Tutor"):
    tutor_user, tutor_headers = _create_user_with_token(db, email, "TUTOR", name)

    profile = TutorProfile(
        user_id=tutor_user.id,
        location="Chennai",
        preferred_teaching_mode="Online",
        languages_spoken=["English", "Tamil"],
        verification_status="MANUAL_REVIEW",
    )
    db.add(profile)
    db.flush()

    edu = Education(
        tutor_profile_id=profile.id,
        highest_degree="Bachelor",
        degree_name="B.E. Computer Science",
        university="Anna University",
        specialization="Software Systems",
        graduation_year=2022,
    )
    db.add(edu)

    exp = TutorExpertise(
        tutor_profile_id=profile.id,
        subjects_taught=["Computer Science"],
        topics_expertise=["Data Structures", "Algorithms"],
        years_of_experience=3,
        skills=["Problem Solving", "Visual Explanations"],
        languages_can_teach_in=["English"],
    )
    db.add(exp)

    cert = Certificate(
        tutor_profile_id=profile.id,
        file_path="certificates/test_degree.pdf",
        original_filename="anna_univ_degree.pdf",
        file_type="application/pdf",
        file_size=102400,
        verification_status="PARTIAL_MATCH",
    )
    db.add(cert)
    db.flush()

    record = VerificationRecord(
        tutor_profile_id=profile.id,
        certificate_id=cert.id,
        verification_status="MANUAL_REVIEW",
        ocr_status="COMPLETED",
        certificate_validation_status="PARTIAL_MATCH",
        security_analysis_status="PASS",
        university_verification_status="NOT_AVAILABLE",
        face_verification_status="NOT_AVAILABLE",
        liveness_status="NOT_AVAILABLE",
        overall_result="MANUAL_REVIEW",
        failure_reason="Minor discrepancy between OCR degree name and declared profile.",
        manual_review_required=True,
        ocr_metadata={
            "name": "Candidate Tutor",
            "university": "Anna University",
            "degree": "Bachelor of Engineering",
            "graduation_year": 2022,
            "confidence_level": "HIGH",
        },
        security_analysis_metadata={
            "status": "PASS",
            "risk_level": "LOW",
            "identifiers": ["Reg.No. 180501016"],
            "risk_flags": [],
        },
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    db.refresh(profile)
    db.refresh(cert)

    return tutor_user, profile, cert, record


# =============================================================================
# 1. ROLE AUTHORIZATION TESTS
# =============================================================================

def test_reviewer_queue_access_authorization(client, db):
    _, reviewer_headers = _create_user_with_token(db, "reviewer_auth@example.com", "VERIFICATION_REVIEWER", "Reviewer Alpha")
    _, tutor_headers = _create_user_with_token(db, "tutor_auth@example.com", "TUTOR", "Tutor Beta")
    _, student_headers = _create_user_with_token(db, "student_auth@example.com", "STUDENT", "Student Gamma")

    # Unauthenticated -> 401 / 403
    res_unauth = client.get("/api/verification/reviewer/manual-reviews")
    assert res_unauth.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    # Student -> 403
    res_student = client.get("/api/verification/reviewer/manual-reviews", headers=student_headers)
    assert res_student.status_code == status.HTTP_403_FORBIDDEN

    # Tutor -> 403
    res_tutor = client.get("/api/verification/reviewer/manual-reviews", headers=tutor_headers)
    assert res_tutor.status_code == status.HTTP_403_FORBIDDEN

    # Reviewer -> 200
    res_reviewer = client.get("/api/verification/reviewer/manual-reviews", headers=reviewer_headers)
    assert res_reviewer.status_code == status.HTTP_200_OK


# =============================================================================
# 2. QUEUE FILTERING TESTS
# =============================================================================

def test_manual_review_queue_filtering(client, db):
    _, reviewer_headers = _create_user_with_token(db, "reviewer_q@example.com", "VERIFICATION_REVIEWER", "Reviewer Q")

    # 1. Create a MANUAL_REVIEW record
    _, _, _, manual_record = _setup_test_tutor(db, "tutor_manual@example.com", "Manual Tutor")

    # 2. Create a VERIFIED record (should NOT appear in queue)
    _, _, _, verified_record = _setup_test_tutor(db, "tutor_verified@example.com", "Verified Tutor")
    verified_record.verification_status = "VERIFIED"
    verified_record.overall_result = "VERIFIED"
    verified_record.manual_review_required = False
    db.commit()

    # 3. Create a FAILED record (should NOT appear in queue)
    _, _, _, failed_record = _setup_test_tutor(db, "tutor_failed@example.com", "Failed Tutor")
    failed_record.verification_status = "FAILED"
    failed_record.overall_result = "FAILED"
    failed_record.manual_review_required = False
    db.commit()

    res = client.get("/api/verification/reviewer/manual-reviews", headers=reviewer_headers)
    assert res.status_code == status.HTTP_200_OK
    queue_items = res.json()

    queue_ids = [item["id"] for item in queue_items]
    assert manual_record.id in queue_ids
    assert verified_record.id not in queue_ids
    assert failed_record.id not in queue_ids

    # Verify item contents
    item = next(i for i in queue_items if i["id"] == manual_record.id)
    assert item["tutor_name"] == "Manual Tutor"
    assert item["tutor_email"] == "tutor_manual@example.com"
    assert item["certificate_filename"] == "anna_univ_degree.pdf"
    assert item["verification_status"] == "MANUAL_REVIEW"
    assert item["manual_review_required"] is True


# =============================================================================
# 3. DETAIL ENDPOINT TESTS
# =============================================================================

def test_get_manual_review_detail_success(client, db):
    _, reviewer_headers = _create_user_with_token(db, "reviewer_det@example.com", "VERIFICATION_REVIEWER", "Reviewer Det")
    _, profile, cert, record = _setup_test_tutor(db, "tutor_det@example.com", "Dr. Evidence")

    res = client.get(f"/api/verification/reviewer/manual-reviews/{record.id}", headers=reviewer_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()

    # Verify structured sections
    assert "verification_record" in data
    assert "tutor" in data
    assert "certificate" in data
    assert "review_history" in data

    # Verification Record
    vr = data["verification_record"]
    assert vr["id"] == record.id
    assert vr["verification_status"] == "MANUAL_REVIEW"
    assert vr["ocr_metadata"]["university"] == "Anna University"
    assert vr["security_analysis_status"] == "PASS"

    # Tutor Profile
    tut = data["tutor"]
    assert tut["full_name"] == "Dr. Evidence"
    assert tut["email"] == "tutor_det@example.com"
    assert len(tut["education"]) == 1
    assert tut["education"][0]["university"] == "Anna University"
    assert tut["expertise"]["years_of_experience"] == 3

    # Certificate
    c = data["certificate"]
    assert c["id"] == cert.id
    assert c["original_filename"] == "anna_univ_degree.pdf"
    assert c["download_url"] == f"/api/verification/reviewer/certificates/{cert.id}/download"


def test_get_manual_review_detail_nonexistent_returns_404(client, db):
    _, reviewer_headers = _create_user_with_token(db, "reviewer_404@example.com", "VERIFICATION_REVIEWER", "Reviewer 404")
    res = client.get("/api/verification/reviewer/manual-reviews/non-existent-uuid", headers=reviewer_headers)
    assert res.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# 4. DECISION BEHAVIOR TESTS (APPROVED, REJECTED, RESUBMISSION_REQUESTED)
# =============================================================================

def test_decision_approved_lifecycle(client, db):
    reviewer_user, reviewer_headers = _create_user_with_token(db, "reviewer_app@example.com", "VERIFICATION_REVIEWER", "Senior Reviewer")
    tutor_user, profile, cert, record = _setup_test_tutor(db, "tutor_app@example.com", "Approved Candidate")

    payload = {
        "decision": "APPROVED",
        "reason": "Verified against official university alumni directory.",
    }
    res = client.post(
        f"/api/verification/reviewer/manual-reviews/{record.id}/decision",
        json=payload,
        headers=reviewer_headers,
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["decision"] == "APPROVED"
    assert data["reviewer_id"] == reviewer_user.id
    assert data["reviewer_name"] == "Senior Reviewer"
    assert data["reason"] == "Verified against official university alumni directory."

    # Verify DB state
    db.refresh(record)
    db.refresh(profile)
    assert record.verification_status == "VERIFIED"
    assert record.overall_result == "VERIFIED"
    assert record.manual_review_required is False
    assert record.completed_at is not None
    assert profile.verification_status == "VERIFIED"
    assert profile.verification_timestamp is not None

    # Verify audit review entry was persisted
    assert len(record.reviews) == 1
    assert record.reviews[0].decision == "APPROVED"
    assert record.reviews[0].reviewer_id == reviewer_user.id

    # Item should be removed from pending queue
    res_q = client.get("/api/verification/reviewer/manual-reviews", headers=reviewer_headers)
    queue_ids = [item["id"] for item in res_q.json()]
    assert record.id not in queue_ids


def test_decision_rejected_lifecycle(client, db):
    reviewer_user, reviewer_headers = _create_user_with_token(db, "reviewer_rej@example.com", "VERIFICATION_REVIEWER", "Reviewer Rej")
    tutor_user, profile, cert, record = _setup_test_tutor(db, "tutor_rej@example.com", "Rejected Candidate")

    payload = {
        "decision": "REJECTED",
        "reason": "Name mismatch could not be reconciled with government ID.",
    }
    res = client.post(
        f"/api/verification/reviewer/manual-reviews/{record.id}/decision",
        json=payload,
        headers=reviewer_headers,
    )
    assert res.status_code == status.HTTP_200_OK

    db.refresh(record)
    db.refresh(profile)
    assert record.verification_status == "FAILED"
    assert record.overall_result == "FAILED"
    assert record.manual_review_required is False
    assert record.failure_reason == "Name mismatch could not be reconciled with government ID."
    assert profile.verification_status == "FAILED"

    assert len(record.reviews) == 1
    assert record.reviews[0].decision == "REJECTED"
    assert record.reviews[0].reason == "Name mismatch could not be reconciled with government ID."


def test_decision_resubmission_requested_lifecycle(client, db):
    reviewer_user, reviewer_headers = _create_user_with_token(db, "reviewer_resub@example.com", "VERIFICATION_REVIEWER", "Reviewer Resub")
    tutor_user, profile, cert, record = _setup_test_tutor(db, "tutor_resub@example.com", "Resub Candidate")

    payload = {
        "decision": "RESUBMISSION_REQUESTED",
        "reason": "Certificate image is blurry. Please upload a clear color scan.",
    }
    res = client.post(
        f"/api/verification/reviewer/manual-reviews/{record.id}/decision",
        json=payload,
        headers=reviewer_headers,
    )
    assert res.status_code == status.HTTP_200_OK

    db.refresh(record)
    db.refresh(profile)
    # Status returns to PENDING to allow tutor re-submission
    assert record.verification_status == "PENDING"
    assert record.overall_result == "PENDING"
    assert record.manual_review_required is False
    assert record.failure_reason == "Certificate image is blurry. Please upload a clear color scan."
    assert profile.verification_status == "PENDING"
    assert profile.verification_timestamp is None

    assert len(record.reviews) == 1
    assert record.reviews[0].decision == "RESUBMISSION_REQUESTED"


# =============================================================================
# 5. VALIDATION & DECISION RESTRICTIONS
# =============================================================================

def test_decision_validation_errors(client, db):
    _, reviewer_headers = _create_user_with_token(db, "reviewer_val@example.com", "VERIFICATION_REVIEWER", "Reviewer Val")
    _, _, _, record = _setup_test_tutor(db, "tutor_val@example.com", "Val Candidate")

    # Invalid decision string
    res_inv = client.post(
        f"/api/verification/reviewer/manual-reviews/{record.id}/decision",
        json={"decision": "MAYBE", "reason": "Not sure"},
        headers=reviewer_headers,
    )
    assert res_inv.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # REJECTED without reason
    res_no_reason_rej = client.post(
        f"/api/verification/reviewer/manual-reviews/{record.id}/decision",
        json={"decision": "REJECTED", "reason": ""},
        headers=reviewer_headers,
    )
    assert res_no_reason_rej.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # RESUBMISSION_REQUESTED without reason
    res_no_reason_resub = client.post(
        f"/api/verification/reviewer/manual-reviews/{record.id}/decision",
        json={"decision": "RESUBMISSION_REQUESTED", "reason": "   "},
        headers=reviewer_headers,
    )
    assert res_no_reason_resub.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_cannot_decide_on_non_manual_review_record(client, db):
    _, reviewer_headers = _create_user_with_token(db, "reviewer_nonpending@example.com", "VERIFICATION_REVIEWER", "Reviewer NonPending")
    _, _, _, record = _setup_test_tutor(db, "tutor_already_ver@example.com", "Already Verified")

    # Mark as already verified
    record.verification_status = "VERIFIED"
    record.manual_review_required = False
    db.commit()

    res = client.post(
        f"/api/verification/reviewer/manual-reviews/{record.id}/decision",
        json={"decision": "APPROVED", "reason": "Late approve"},
        headers=reviewer_headers,
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "not currently pending manual review" in res.json()["detail"]


# =============================================================================
# 6. AUDIT HISTORY & MULTIPLE ACTIONS PRESERVATION
# =============================================================================

def test_audit_history_preserves_multiple_reviews(client, db):
    rev_1, headers_1 = _create_user_with_token(db, "rev_1@example.com", "VERIFICATION_REVIEWER", "First Reviewer")
    rev_2, headers_2 = _create_user_with_token(db, "rev_2@example.com", "VERIFICATION_REVIEWER", "Second Reviewer")
    _, profile, _, record = _setup_test_tutor(db, "tutor_multi_audit@example.com", "Multi Audit Candidate")

    # 1. First review: Request resubmission
    client.post(
        f"/api/verification/reviewer/manual-reviews/{record.id}/decision",
        json={"decision": "RESUBMISSION_REQUESTED", "reason": "Please upload higher resolution."},
        headers=headers_1,
    )

    # 2. Simulate tutor re-triggering automated pipeline which hits MANUAL_REVIEW again
    db.refresh(record)
    record.verification_status = "MANUAL_REVIEW"
    record.manual_review_required = True
    db.commit()

    # 3. Second review: Approve
    client.post(
        f"/api/verification/reviewer/manual-reviews/{record.id}/decision",
        json={"decision": "APPROVED", "reason": "Re-uploaded scan is clear and verified."},
        headers=headers_2,
    )

    # 4. Fetch detail and check audit history
    res = client.get(f"/api/verification/reviewer/manual-reviews/{record.id}", headers=headers_1)
    data = res.json()
    history = data["review_history"]

    assert len(history) == 2
    # Verify chronological ordering and reviewer attribution
    assert history[0]["decision"] == "APPROVED"
    assert history[0]["reviewer_name"] == "Second Reviewer"
    assert history[1]["decision"] == "RESUBMISSION_REQUESTED"
    assert history[1]["reviewer_name"] == "First Reviewer"


# =============================================================================
# 7. EDGE CASES: NO PHOTO, MISSING METADATA
# =============================================================================

def test_edge_case_no_photo_and_sparse_metadata(client, db):
    _, reviewer_headers = _create_user_with_token(db, "reviewer_sparse@example.com", "VERIFICATION_REVIEWER", "Reviewer Sparse")
    tutor_user, tutor_headers = _create_user_with_token(db, "tutor_sparse@example.com", "TUTOR", "Sparse Tutor")

    profile = TutorProfile(user_id=tutor_user.id, verification_status="MANUAL_REVIEW")
    db.add(profile)
    db.flush()

    cert = Certificate(
        tutor_profile_id=profile.id,
        file_path="certificates/sparse.pdf",
        original_filename="sparse_cert.pdf",
        file_type="application/pdf",
        file_size=50000,
    )
    db.add(cert)
    db.flush()

    # Record with completely missing metadata and NOT_AVAILABLE face modality
    record = VerificationRecord(
        tutor_profile_id=profile.id,
        certificate_id=cert.id,
        verification_status="MANUAL_REVIEW",
        manual_review_required=True,
        face_verification_status="NOT_AVAILABLE",
        liveness_status="NOT_AVAILABLE",
        ocr_metadata=None,
        security_analysis_metadata=None,
    )
    db.add(record)
    db.commit()

    # Querying detail must NOT crash
    res = client.get(f"/api/verification/reviewer/manual-reviews/{record.id}", headers=reviewer_headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["verification_record"]["face_verification_status"] == "NOT_AVAILABLE"
    assert data["verification_record"]["ocr_metadata"] is None
    assert data["tutor"]["education"] == []
