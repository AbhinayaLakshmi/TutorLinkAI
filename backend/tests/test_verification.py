import io
from fastapi import status
from backend.app.core.config import settings
from backend.app.models.verification import VerificationRecord
from backend.app.models.tutor import TutorProfile
from backend.app.services.security import DocumentSecurityService

def _get_headers(client, email):
    # Helper to register, verify, login and get headers
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Tutor User",
            "phone_number": "1234567890",
            "role": "TUTOR"
        }
    )
    otp = settings.TEST_OTP_STORE[email]
    login_res = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_unauthorized_access(client):
    res = client.get("/api/verification/tutor/me/status")
    # OAuth2 reusable Bearer scheme returns 403 on missing authorization headers
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_student_forbidden_access(client):
    # Register student
    email = "student_verify@example.com"
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Student User",
            "phone_number": "1234567890",
            "role": "STUDENT"
        }
    )
    otp = settings.TEST_OTP_STORE[email]
    login_res = client.post("/api/auth/verify-otp", json={"email": email, "otp": otp})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/verification/tutor/me/status", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN

def test_start_verification_missing_certificate(client):
    headers = _get_headers(client, "nocert@example.com")
    
    # Try starting without uploading certificate
    res = client.post("/api/verification/tutor/me/start", headers=headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "No certificate uploaded" in res.json()["detail"]

def test_start_verification_success_match(client):
    headers = _get_headers(client, "success_match@example.com")
    
    # Save education info first (to match mock MIT certificate values)
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
    
    # Upload mock MIT certificate
    file_payload = {"file": ("mit_certificate.png", io.BytesIO(b"image bytes"), "image/png")}
    client.post("/api/onboarding/tutor/me/certificate", headers=headers, files=file_payload)

    # Start verification
    res = client.post("/api/verification/tutor/me/start", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    
    # Assert Step-by-Step validation details
    assert data["ocr_status"] == "COMPLETED"
    assert data["certificate_validation_status"] == "MATCH"
    # Verification overall result stays PENDING (Reserved for future stages)
    assert data["verification_status"] == "PENDING"
    assert data["overall_result"] == "PENDING"
    assert data["manual_review_required"] is False

    # Get status endpoint check
    res_status = client.get("/api/verification/tutor/me/status", headers=headers)
    assert res_status.status_code == status.HTTP_200_OK
    status_data = res_status.json()
    assert status_data["verification_status"] == "PENDING"
    assert status_data["certificate_validation_status"] == "MATCH"

def test_start_verification_partial_match(client):
    headers = _get_headers(client, "partial@example.com")
    
    # Save education details with slight discrepancy (Stanford, Jane Stanford name)
    client.put(
        "/api/onboarding/tutor/me",
        headers=headers,
        json={
            "location": "Palo Alto",
            "education": [
                {
                    "highest_degree": "Master",
                    "degree_name": "Master of Computer Science",
                    "university": "Stanford University",
                    "graduation_year": 2021
                }
            ]
        }
    )
    
    # Upload mock Stanford certificate (which has candidate name: Jane Stanford)
    # The tutor's registered full name is "Tutor User". This leads to name mismatch/partial match.
    file_payload = {"file": ("stanford_cert.png", io.BytesIO(b"image bytes"), "image/png")}
    client.post("/api/onboarding/tutor/me/certificate", headers=headers, files=file_payload)

    # Start verification
    res = client.post("/api/verification/tutor/me/start", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    
    # Assert Partial Match triggers Manual Review
    assert data["certificate_validation_status"] == "PARTIAL_MATCH"
    assert data["verification_status"] == "MANUAL_REVIEW"
    assert data["overall_result"] == "MANUAL_REVIEW"
    assert data["manual_review_required"] is True
    assert "Fuzzy profile comparison found minor discrepancies" in data["failure_reason"]

def test_start_verification_hard_mismatch(client):
    headers = _get_headers(client, "mismatch@example.com")
    
    # Save mismatching education details
    client.put(
        "/api/onboarding/tutor/me",
        headers=headers,
        json={
            "location": "Boston",
            "education": [
                {
                    "highest_degree": "Bachelor",
                    "degree_name": "B.Sc. Physics",
                    "university": "UChicago",
                    "graduation_year": 2019
                }
            ]
        }
    )
    
    # Upload mismatching certificate (which has candidate name "Completely Different Name")
    file_payload = {"file": ("mismatch_cert.png", io.BytesIO(b"image bytes"), "image/png")}
    client.post("/api/onboarding/tutor/me/certificate", headers=headers, files=file_payload)

    # Start verification
    res = client.post("/api/verification/tutor/me/start", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    
    # Hard name mismatch triggers FAILED status
    assert data["certificate_validation_status"] == "MISMATCH"
    assert data["verification_status"] == "FAILED"
    assert data["overall_result"] == "FAILED"
    assert data["manual_review_required"] is False
    assert "Candidate name discrepancy" in data["failure_reason"]

def test_start_verification_low_confidence(client):
    headers = _get_headers(client, "lowconf@example.com")
    
    client.put(
        "/api/onboarding/tutor/me",
        headers=headers,
        json={
            "location": "Chicago",
            "education": [
                {
                    "highest_degree": "Bachelor",
                    "degree_name": "B.Sc",
                    "university": "Unknown College",
                    "graduation_year": 2020
                }
            ]
        }
    )
    
    # Upload file that triggers low confidence parser mock
    file_payload = {"file": ("low_confidence_file.png", io.BytesIO(b"image bytes"), "image/png")}
    client.post("/api/onboarding/tutor/me/certificate", headers=headers, files=file_payload)

    # Start verification
    res = client.post("/api/verification/tutor/me/start", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    
    # Low confidence routes to Manual Review
    assert data["certificate_validation_status"] == "INSUFFICIENT_DATA"
    assert data["verification_status"] == "MANUAL_REVIEW"
    assert data["overall_result"] == "MANUAL_REVIEW"
    assert data["manual_review_required"] is True
    assert "low-confidence" in data["failure_reason"]

def test_security_unit_pdf_with_metadata(tmp_path):
    # Test file with unexpected editor metadata
    file_path = str(tmp_path / "unexpected_editor.pdf")
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.4 ... dummy pdf ...")
    
    text_lines = ["Reg.No. 12345", "SI.No. 98765", "September 2023", "MAY 2022"]
    res = DocumentSecurityService.analyze_document(file_path, text_lines)
    
    assert res["status"] == "SUSPICIOUS"
    assert res["metadata"]["risk_score"] == 15
    flags = [f["rule"] for f in res["metadata"]["flags"]]
    assert "unexpected_editor_metadata" in flags
    assert "missing_identifiers" not in flags

def test_security_unit_pdf_no_metadata(tmp_path):
    # Test file with no metadata and missing identifiers
    file_path = str(tmp_path / "normal.pdf")
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.4 ... dummy pdf ...")
        
    text_lines = ["Some text without any serial or roll numbers", "Year 2022"]
    res = DocumentSecurityService.analyze_document(file_path, text_lines)
    
    # Missing identifiers adds 15 risk -> SUSPICIOUS
    assert res["status"] == "SUSPICIOUS"
    assert res["metadata"]["risk_score"] == 15
    flags = [f["rule"] for f in res["metadata"]["flags"]]
    assert "missing_identifiers" in flags

def test_security_unit_image_certificate(tmp_path):
    # Image files return metadata as unavailable
    file_path = str(tmp_path / "image.png")
    with open(file_path, "wb") as f:
        f.write(b"PNG ... dummy image ...")
        
    text_lines = ["Reg.No. 12345", "SI.No. 98765"]
    res = DocumentSecurityService.analyze_document(file_path, text_lines)
    
    assert res["status"] == "PASS"  # Scanned document has 0 risk points
    assert res["metadata"]["metadata"]["has_native_text"] is False
    flags = [f["rule"] for f in res["metadata"]["flags"]]
    assert "scanned_document" in flags

def test_security_unit_identifiers_extraction():
    # Verify extraction logic of various certificate identifiers
    text_lines = [
        "Reg.No. 180501016/RG",
        "SI.No: MJ",
        "1846723",
        "admitted to degree in MAY 2022",
        "given under seal September 2023",
        "VU136410400015"
    ]
    identifiers = DocumentSecurityService._extract_identifiers(text_lines)
    assert identifiers["registration_number"] == "180501016/RG"
    assert identifiers["serial_number"] == "MJ 1846723"
    assert identifiers["certificate_number"] == "VU136410400015"
    assert identifiers["issue_date"] == "September 2023"

def test_security_unit_suspicious_metadata(tmp_path):
    # Test suspicious modification tools (e.g. iLovePDF)
    file_path = str(tmp_path / "ilovepdf.pdf")
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.4 ... dummy pdf ...")
        
    text_lines = ["Reg.No. 12345", "SI.No. 98765"]
    res = DocumentSecurityService.analyze_document(file_path, text_lines)
    
    assert res["status"] == "SUSPICIOUS"
    assert res["metadata"]["risk_score"] == 20
    flags = [f["rule"] for f in res["metadata"]["flags"]]
    assert "suspicious_modification" in flags

def test_security_unit_future_graduation(tmp_path):
    # Test graduation date set in the future (e.g. 2030)
    file_path = str(tmp_path / "future_graduation.pdf")
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.4 ... dummy pdf ...")
        
    text_lines = ["Reg.No. 12345", "SI.No. 98765", "examination held in MAY 2030"]
    res = DocumentSecurityService.analyze_document(file_path, text_lines)
    
    assert res["status"] == "SUSPICIOUS"
    assert res["metadata"]["risk_score"] == 25
    flags = [f["rule"] for f in res["metadata"]["flags"]]
    assert "future_graduation_date" in flags

def test_security_unit_contradictory_issue_date(tmp_path):
    # Test graduation after issue date
    file_path = str(tmp_path / "contradictory_issue_date.pdf")
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.4 ... dummy pdf ...")
        
    text_lines = ["Reg.No. 12345", "SI.No. 98765", "examination held in MAY 2025", "issued September 2023"]
    res = DocumentSecurityService.analyze_document(file_path, text_lines)
    
    assert res["status"] == "SUSPICIOUS"
    assert res["metadata"]["risk_score"] == 25
    flags = [f["rule"] for f in res["metadata"]["flags"]]
    assert "contradictory_issue_date" in flags

def test_start_verification_security_demotion(client):
    # Regression and integration test: Profile MATCH + Security SUSPICIOUS -> overall MANUAL_REVIEW
    headers = _get_headers(client, "secdemoted@example.com")
    
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
    
    # Upload mock MIT certificate but name it so that it triggers unexpected editor metadata in tests
    file_payload = {"file": ("mit_unexpected_editor.pdf", io.BytesIO(b"pdf bytes"), "application/pdf")}
    client.post("/api/onboarding/tutor/me/certificate", headers=headers, files=file_payload)

    # Start verification
    res = client.post("/api/verification/tutor/me/start", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    
    # Security is SUSPICIOUS, so profile MATCH is demoted to MANUAL_REVIEW overall
    assert data["certificate_validation_status"] == "MATCH"
    assert data["security_analysis_status"] == "SUSPICIOUS"
    assert data["verification_status"] == "MANUAL_REVIEW"
    assert data["overall_result"] == "MANUAL_REVIEW"
    assert data["manual_review_required"] is True
    assert "security_analysis_metadata" in data
    assert data["security_analysis_metadata"]["risk_score"] == 15
