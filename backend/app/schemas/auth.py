import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., description="Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special char")
    full_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., description="Phone number must contain exactly 10 digits")
    role: str = Field(..., description="Role must be STUDENT or TUTOR")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ("STUDENT", "TUTOR"):
            raise ValueError("Role must be either STUDENT or TUTOR")
        return v_upper

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Strip out any non-digits
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 10:
            raise ValueError("Phone number must contain exactly 10 digits")
        return digits

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OtpVerify(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="OTP must be exactly 6 characters")


class OtpResend(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    role: str
    onboarding_status: str
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
