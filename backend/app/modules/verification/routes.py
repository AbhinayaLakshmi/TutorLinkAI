from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.tutor import TutorProfile, Certificate
from backend.app.models.verification import VerificationRecord
from backend.app.schemas.verification import VerificationRecordOut, VerificationStatusOut
from backend.app.schemas.tutor import CertificateOutSchema
from backend.app.services.auth import get_current_user, require_role
from backend.app.modules.verification.services import verification as verification_service
from backend.app.services.live_face import LiveFaceService, LiveFaceUpload

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
        import logging
        logger = logging.getLogger("live_face_route")
        logger.info(f"Received live face check request. Action: {payload.action}")

        result = service.verify_live_face(payload.frame_straight, payload.frame_action, payload.action)
        logger.info(f"verify_live_face result: {result}")
        
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
