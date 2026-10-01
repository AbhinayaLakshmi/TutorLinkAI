import os
import logging
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.tutor import TutorProfile, Certificate
from backend.app.models.verification import VerificationRecord
from backend.app.schemas.verification import (
    VerificationRecordOut,
    VerificationStatusOut,
    ManualReviewQueueItem,
    ManualReviewDetail,
    VerificationReviewCreate,
    VerificationReviewOut,
)
from backend.app.schemas.tutor import CertificateOutSchema
from backend.app.services.auth import get_current_user, require_role
from backend.app.modules.verification.services import verification as verification_service
from backend.app.services.live_face import LiveFaceService, LiveFaceUpload
from backend.app.services.face import CertificateFaceService
from backend.app.services.face_embedder import FaceEmbedder

logger = logging.getLogger("live_face_route")

router = APIRouter(prefix="/api/verification", tags=["verification"])

@router.get(
    "/tutor/me/status",
    response_model=VerificationStatusOut,
    dependencies=[Depends(require_role("TUTOR"))]
)
def get_verification_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Tutor profile not found")

    record = db.query(VerificationRecord).filter(VerificationRecord.tutor_profile_id == profile.id).first()
    if not record:
        # Default pending state if pipeline was never triggered
        return {
            "verification_status": profile.verification_status or "PENDING",
            "overall_result": "PENDING",
            "manual_review_required": False,
            "ocr_status": "PENDING",
            "certificate_validation_status": "PENDING"
        }

    return {
        "verification_status": record.verification_status,
        "overall_result": record.overall_result,
        "manual_review_required": record.manual_review_required,
        "ocr_status": record.ocr_status,
        "certificate_validation_status": record.certificate_validation_status
    }


@router.get(
    "/tutor/me",
    response_model=VerificationRecordOut,
    dependencies=[Depends(require_role("TUTOR"))]
)
def get_verification_record(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Tutor profile not found")

    record = db.query(VerificationRecord).filter(VerificationRecord.tutor_profile_id == profile.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="No verification record exists for this tutor.")

    return record


@router.post(
    "/tutor/me/start",
    response_model=VerificationRecordOut,
    dependencies=[Depends(require_role("TUTOR"))]
)
def start_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Tutor profile not found")

    try:
        record = verification_service.initiate_verification(db, profile.id)
        return record
    except Exception as e:
        if hasattr(e, "status_code"):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/tutor/me/certificate",
    response_model=List[CertificateOutSchema],
    dependencies=[Depends(require_role("TUTOR"))]
)
def get_tutor_certificates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Tutor profile not found")

    return profile.certificates


@router.post(
    "/tutor/me/live-face",
    dependencies=[Depends(require_role("TUTOR"))]
)
def submit_live_face_verification(
    payload: LiveFaceUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Tutor profile not found")

    record = db.query(VerificationRecord).filter(VerificationRecord.tutor_profile_id == profile.id).first()
    if not record:
        raise HTTPException(
            status_code=400, 
            detail="No verification record exists. Please start certificate validation pipeline first."
        )

    try:
        service = LiveFaceService()
        logger.info(f"Received live face check request. Action: {payload.action}")

        result = service.verify_live_face(payload.frame_straight, payload.frame_action, payload.action)
        logger.info(f"verify_live_face result: {result}")
        
        # Pop face_crop so that raw biometric NumPy array is NEVER serialized into the API response
        live_face_crop = result.pop("face_crop", None)

        # In-memory identity similarity calculation (research signal only, no decision threshold applied)
        identity_similarity = None
        if live_face_crop is not None and record.certificate:
            try:
                cert_file_path = record.certificate.file_path
                if cert_file_path:
                    cert_path = os.path.join(settings.UPLOAD_DIR, cert_file_path)
                    if os.path.exists(cert_path):
                        cert_face_res = CertificateFaceService().extract_certificate_face(
                            cert_path,
                            record.certificate.original_filename
                        )
                        cert_crop = cert_face_res.get("face_crop")
                        if cert_crop is not None:
                            embedder = FaceEmbedder()
                            cert_emb = embedder.extract_embedding(cert_crop)
                            live_emb = embedder.extract_embedding(live_face_crop)
                            identity_similarity = embedder.compute_cosine_similarity(cert_emb, live_emb)
                            logger.info(f"Certificate-to-live identity similarity: {identity_similarity:.4f}")
            except Exception as face_err:
                logger.warning(f"Certificate-to-live identity comparison non-fatal error: {face_err}")

        if identity_similarity is not None:
            result["identity_similarity"] = float(identity_similarity)

        # Save verification results
        record.face_verification_status = result["face_quality"]
        record.liveness_status = result["liveness_status"]
        
        # Evaluate promotion to VERIFIED (idempotent and atomic)
        if (
            record.ocr_status == "COMPLETED"
            and record.certificate_validation_status == "MATCH"
            and record.security_analysis_status == "PASS"
            and record.liveness_status == "PASSED"
        ):
            record.verification_status = "VERIFIED"
            record.overall_result = "VERIFIED"
            profile.verification_status = "VERIFIED"
            
        db.commit()
        
        return result
    except ValueError as val_err:
        import traceback
        traceback.print_exc()
        import logging
        logging.getLogger("live_face_route").error(f"ValueError: {type(val_err).__name__}: {str(val_err)}")
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        import traceback
        traceback.print_exc()
        import logging
        logging.getLogger("live_face_route").error(f"Exception: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal face processing error: {str(e)}")


# =============================================================================
# VERIFICATION REVIEWER ENDPOINTS
# =============================================================================

@router.get(
    "/reviewer/manual-reviews",
    response_model=List[ManualReviewQueueItem],
    dependencies=[Depends(require_role("VERIFICATION_REVIEWER"))]
)
def list_pending_manual_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the list of all verification records currently pending manual review.
    Accessible only to authorized VERIFICATION_REVIEWER.
    """
    return verification_service.list_manual_review_queue(db)


@router.get(
    "/reviewer/manual-reviews/{verification_id}",
    response_model=ManualReviewDetail,
    dependencies=[Depends(require_role("VERIFICATION_REVIEWER"))]
)
def get_manual_review_detail(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns structured evidence summary (tutor profile, education, certificate,
    OCR metadata, security analysis, face/liveness signals, and review history)
    for a specific verification record.
    """
    try:
        return verification_service.get_manual_review_detail(db, verification_id)
    except Exception as e:
        if hasattr(e, "status_code"):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/reviewer/manual-reviews/{verification_id}/decision",
    response_model=VerificationReviewOut,
    dependencies=[Depends(require_role("VERIFICATION_REVIEWER"))]
)
def submit_manual_review_decision(
    verification_id: str,
    payload: VerificationReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Applies an authorized decision (APPROVED, REJECTED, RESUBMISSION_REQUESTED)
    to a pending manual review, updates profile/verification status, and records an audit log.
    """
    try:
        return verification_service.resolve_manual_review(
            db=db,
            verification_id=verification_id,
            reviewer_user=current_user,
            decision=payload.decision,
            reason=payload.reason
        )
    except Exception as e:
        if hasattr(e, "status_code"):
            raise e
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/reviewer/certificates/{certificate_id}/download",
    dependencies=[Depends(require_role("VERIFICATION_REVIEWER"))]
)
def download_certificate_for_review(
    certificate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Serves certificate file securely to authorized reviewers.
    """
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")

    file_path = os.path.join(settings.UPLOAD_DIR, certificate.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Certificate file not found on disk")

    return FileResponse(
        path=file_path,
        filename=certificate.original_filename,
        media_type=certificate.file_type or "application/octet-stream"
    )

