import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, token: str) -> bool:
    verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={token}"

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP not configured — verification email not sent. "
            "Verify URL: %s",
            verify_url,
        )
        return False

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; padding: 2rem; background: #f4f4f4;">
  <div style="max-width: 480px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 2rem;">
    <h2 style="margin-top: 0;">Verify your email</h2>
    <p>Thanks for signing up! Click the button below to verify your email address.</p>
    <a href="{verify_url}"
       style="display: inline-block; background: #131921; color: #fff; padding: 12px 24px;
              border-radius: 6px; text-decoration: none; font-weight: bold; margin: 16px 0;">
      Verify Email
    </a>
    <p style="color: #666; font-size: 14px;">Or copy this link into your browser:<br>
    <a href="{verify_url}" style="color: #007185; word-break: break-all;">{verify_url}</a></p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
    <p style="color: #999; font-size: 12px;">If you didn't create this account, you can ignore this email.</p>
  </div>
</body>
</html>"""

    msg = MIMEText(html, "html")
    msg["Subject"] = "Verify your email — Agentic Commerce"
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Verification email sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Failed to send verification email to %s", to_email)
        return False


def send_password_reset_email(to_email: str, token: str) -> bool:
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP not configured — password reset email not sent. "
            "Reset URL: %s",
            reset_url,
        )
        return False

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; padding: 2rem; background: #f4f4f4;">
  <div style="max-width: 480px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 2rem;">
    <h2 style="margin-top: 0;">Reset your password</h2>
    <p>Click the button below to reset your password. This link expires in 1 hour.</p>
    <a href="{reset_url}"
       style="display: inline-block; background: #131921; color: #fff; padding: 12px 24px;
              border-radius: 6px; text-decoration: none; font-weight: bold; margin: 16px 0;">
      Reset Password
    </a>
    <p style="color: #666; font-size: 14px;">Or copy this link into your browser:<br>
    <a href="{reset_url}" style="color: #007185; word-break: break-all;">{reset_url}</a></p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
    <p style="color: #999; font-size: 12px;">If you didn't request this, you can ignore this email.</p>
  </div>
</body>
</html>"""

    msg = MIMEText(html, "html")
    msg["Subject"] = "Reset your password — Agentic Commerce"
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Password reset email sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
        return False
