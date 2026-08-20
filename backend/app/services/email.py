import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.core.config import settings

logger = logging.getLogger("email_service")

def send_otp_email(to_email: str, otp: str) -> None:
    """
    Sends a verification OTP email using smtplib over SMTP (TLS).
    Raises ValueError/RuntimeError if SMTP is missing or fails.
    """
    # 1. Enforce SMTP credentials exist in production/actual execution
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        logger.error("SMTP Configuration is incomplete. Ensure SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD are set.")
        raise ValueError("SMTP email service is not configured. Please contact the administrator.")
        
    # 2. Build professional MIME email
    msg = MIMEMultipart()
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME}>"
    msg["To"] = to_email
    msg["Subject"] = "TutorLinkAI — Verify Your Email"
    
    body = f"""Hello,

Welcome to TutorLinkAI.

Use the following verification code to verify your email:

{otp}

This code expires in 10 minutes.

Do not share this code with anyone.

Regards,
TutorLinkAI Team"""

    msg.attach(MIMEText(body, "plain"))
    
    # 3. Connect to server and deliver
    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        server.ehlo()
        if settings.SMTP_USE_TLS:
            server.starttls()
            server.ehlo()
        
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME, to_email, msg.as_string())
        server.quit()
        logger.info(f"Successfully sent OTP email to {to_email}")
    except Exception as e:
        logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
        raise RuntimeError("Failed to deliver verification email. Please check SMTP settings.")
