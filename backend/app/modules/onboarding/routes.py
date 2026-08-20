import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.core.exceptions import BadRequestException, ResourceNotFoundException, RoleForbiddenException
from backend.app.database.session import get_db
from backend.app.models.user import User, OTPVerification
from backend.app.models.tutor import Certificate
from backend.app.schemas.auth import UserRegister, UserLogin, Token, UserOut, OtpVerify, OtpResend
from backend.app.schemas.student import StudentProfileUpdate, StudentProfileOut
from backend.app.schemas.tutor import TutorProfileUpdate, TutorProfileOut, CertificateOutSchema
from backend.app.services.auth import get_current_user, require_role
from backend.app.services.upload import save_uploaded_file
from backend.app.services.email import send_otp_email
from backend.app.modules.onboarding.services import onboarding as onboarding_service

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
onboarding_router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

# Helper function to generate and save OTP
def generate_and_save_otp(user_id: str, email: str, db: Session) -> str:
    # 1. Generate 6 digit random number
    otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
    
    # 2. Hash it
    hashed_otp = hashlib.sha256(otp_code.encode("utf-8")).hexdigest()
    
    # 3. Expiry and last sent timestamp
    expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minutes expiry
    
    # 4. Check rate limiting (60s cooldown)
    otp_record = db.query(OTPVerification).filter(OTPVerification.user_id == user_id).first()
    if otp_record:
        if datetime.utcnow() - otp_record.last_sent_at < timedelta(seconds=60):
            wait_time = 60 - int((datetime.utcnow() - otp_record.last_sent_at).total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait_time} seconds before requesting a new OTP."
            )
            
    # 5. Deliver plaintext OTP through email service first
    try:
        send_otp_email(email, otp_code)
    except Exception as e:
        # SMTP configuration missing or failed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deliver verification email: {str(e)}"
        )
    
    # 6. If email sending succeeded, save OTP in database
    if otp_record:
        otp_record.hashed_otp = hashed_otp
        otp_record.expires_at = expires_at
        otp_record.attempts = 0
        otp_record.last_sent_at = datetime.utcnow()
    else:
        otp_record = OTPVerification(
            user_id=user_id,
            hashed_otp=hashed_otp,
            expires_at=expires_at,
            attempts=0,
            last_sent_at=datetime.utcnow()
        )
        db.add(otp_record)
        
    db.commit()
    
    # Cache plain OTP for automated testing ONLY
    settings.TEST_OTP_STORE[email] = otp_code
    
    return otp_code


# --- AUTHENTICATION ROUTES ---

@auth_router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    normalized_email = user_in.email.strip().lower()
    
    # Check if duplicate email
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise BadRequestException(detail="Email already registered.")
    
    # Create user
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        email=normalized_email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        phone_number=user_in.phone_number,
        role=user_in.role.upper(),
        onboarding_status="INCOMPLETE",
        email_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Pre-create profiles skeleton
    if new_user.role == "STUDENT":
        onboarding_service.get_student_profile(db, new_user.id)
    else:
        onboarding_service.get_tutor_profile(db, new_user.id)
        
    # Generate, deliver, and save initial OTP
    generate_and_save_otp(new_user.id, normalized_email, db)
    
    return new_user

@auth_router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    normalized_email = user_in.email.strip().lower()
    
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    token = create_access_token(subject=user.id, role=user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@auth_router.post("/verify-otp", response_model=Token)
def verify_otp(verify_in: OtpVerify, db: Session = Depends(get_db)):
    normalized_email = verify_in.email.strip().lower()
    
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise ResourceNotFoundException("User not found")
        
    otp_record = db.query(OTPVerification).filter(OTPVerification.user_id == user.id).first()
    if not otp_record:
        raise BadRequestException("No active OTP found. Please request a new OTP.")
        
    # Expiry Check
    if otp_record.expires_at < datetime.utcnow():
        db.delete(otp_record)
        db.commit()
        raise BadRequestException("OTP has expired. Please request a new OTP.")
        
    # Attempts Check
    if otp_record.attempts >= 5:
        db.delete(otp_record)
        db.commit()
        raise BadRequestException("Too many failed attempts. Please request a new OTP.")
        
    # Hash check
    input_hashed = hashlib.sha256(verify_in.otp.encode("utf-8")).hexdigest()
    if input_hashed == otp_record.hashed_otp:
        # Match
        user.email_verified = True
        db.delete(otp_record)
        db.commit()
        db.refresh(user)
        
        # Generate authenticated JWT
        token = create_access_token(subject=user.id, role=user.role)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user
        }
    else:
        # No Match, increment attempts
        otp_record.attempts += 1
        db.commit()
        remaining = 5 - otp_record.attempts
        if remaining <= 0:
            db.delete(otp_record)
            db.commit()
            raise BadRequestException("Too many failed attempts. Please request a new OTP.")
        raise BadRequestException(f"Invalid OTP code. Attempts remaining: {remaining}")

@auth_router.post("/resend-otp")
def resend_otp(resend_in: OtpResend, db: Session = Depends(get_db)):
    normalized_email = resend_in.email.strip().lower()
    
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise ResourceNotFoundException("User not found")
        
    generate_and_save_otp(user.id, normalized_email, db)
    return {"message": "OTP has been resent to your email address."}

@auth_router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# --- ONBOARDING STUDENT ROUTES ---

@onboarding_router.get(
    "/student/me", 
    response_model=StudentProfileOut,
    dependencies=[Depends(require_role("STUDENT"))]
)
def get_student_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return onboarding_service.get_student_profile(db, current_user.id)

@onboarding_router.put(
    "/student/me", 
    response_model=StudentProfileOut,
    dependencies=[Depends(require_role("STUDENT"))]
)
def update_student_my_profile(
    profile_data: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return onboarding_service.update_student_profile(db, current_user.id, profile_data)

@onboarding_router.post(
    "/student/complete", 
    response_model=UserOut,
    dependencies=[Depends(require_role("STUDENT"))]
)
def submit_student_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return onboarding_service.complete_student_onboarding(db, current_user.id)


# --- ONBOARDING TUTOR ROUTES ---

@onboarding_router.get(
    "/tutor/me", 
    response_model=TutorProfileOut,
    dependencies=[Depends(require_role("TUTOR"))]
)
def get_tutor_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return onboarding_service.get_tutor_profile(db, current_user.id)

@onboarding_router.put(
    "/tutor/me", 
    response_model=TutorProfileOut,
    dependencies=[Depends(require_role("TUTOR"))]
)
def update_tutor_my_profile(
    profile_data: TutorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return onboarding_service.update_tutor_profile(db, current_user.id, profile_data)

@onboarding_router.post(
    "/tutor/me/profile-picture", 
    response_model=TutorProfileOut,
    dependencies=[Depends(require_role("TUTOR"))]
)
def upload_tutor_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dest_path, filename, size = save_uploaded_file(
        file=file,
        subfolder="profile_pics",
        max_size_bytes=settings.MAX_PROFILE_PIC_SIZE_BYTES,
        allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS
    )
    relative_path = os.path.relpath(dest_path, settings.UPLOAD_DIR)
    return onboarding_service.update_tutor_profile_picture(db, current_user.id, relative_path)

@onboarding_router.post(
    "/tutor/me/certificate", 
    response_model=CertificateOutSchema,
    dependencies=[Depends(require_role("TUTOR"))]
)
def upload_tutor_certificate(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dest_path, filename, size = save_uploaded_file(
        file=file,
        subfolder="certificates",
        max_size_bytes=settings.MAX_CERTIFICATE_SIZE_BYTES,
        allowed_extensions=settings.ALLOWED_DOCUMENT_EXTENSIONS
    )
    relative_path = os.path.relpath(dest_path, settings.UPLOAD_DIR)
    file_type = file.content_type or "application/octet-stream"
    
    return onboarding_service.add_tutor_certificate(
        db=db,
        user_id=current_user.id,
        relative_path=relative_path,
        original_filename=filename,
        file_type=file_type,
        file_size=size
    )

@onboarding_router.get(
    "/tutor/me/certificates/{certificate_id}/download",
    dependencies=[Depends(require_role("TUTOR"))]
)
def download_tutor_certificate(
    certificate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tutor_profile = onboarding_service.get_tutor_profile(db, current_user.id)
    cert = db.query(Certificate).filter(
        Certificate.id == certificate_id,
        Certificate.tutor_profile_id == tutor_profile.id
    ).first()
    
    if not cert:
        raise ResourceNotFoundException("Certificate not found or unauthorized")
        
    full_path = os.path.join(settings.UPLOAD_DIR, cert.file_path)
    if not os.path.exists(full_path):
        raise ResourceNotFoundException("Certificate file not found on disk")
        
    return FileResponse(
        path=full_path,
        filename=cert.original_filename,
        media_type=cert.file_type
    )

@onboarding_router.post(
    "/tutor/complete", 
    response_model=UserOut,
    dependencies=[Depends(require_role("TUTOR"))]
)
def submit_tutor_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return onboarding_service.complete_tutor_onboarding(db, current_user.id)
