import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "TutorLinkAI Onboarding API"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/tutor_platform"
    )
    
    # JWT security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # OTP Mock/Test store
    TEST_OTP_STORE = {}
    
    # SMTP Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "TutorLinkAI")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # File upload configurations
    UPLOAD_DIR: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
    )
    MAX_CERTIFICATE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB
    MAX_PROFILE_PIC_SIZE_BYTES: int = 2 * 1024 * 1024  # 2MB
    
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png"}
    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

settings = Settings()
