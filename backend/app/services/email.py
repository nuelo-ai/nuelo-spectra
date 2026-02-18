"""Email service for sending password reset and other emails via SMTP."""

import hashlib
import logging
import secrets
from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import Settings

logger = logging.getLogger(__name__)

# Jinja2 template environment
_template_dir = Path(__file__).parent.parent / "templates" / "email"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_template_dir)),
    autoescape=select_autoescape(["html"]),
)


def is_smtp_configured(settings: Settings) -> bool:
    """Check if SMTP is configured for production email sending.

    Returns True only when all required SMTP settings are provided.
    When False, email functions fall back to console logging (dev mode).
    """
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_pass)


def create_reset_token() -> tuple[str, str]:
    """Generate a cryptographically secure password reset token.

    Returns:
        Tuple of (raw_token, token_hash) where raw_token is sent to the user
        and token_hash is stored in the database.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


def verify_token_hash(raw_token: str, stored_hash: str) -> bool:
    """Verify a raw token against a stored SHA-256 hash.

    Uses constant-time comparison to prevent timing attacks.
    """
    computed_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return secrets.compare_digest(computed_hash, stored_hash)


async def send_password_reset_email(
    to_email: str,
    first_name: str | None,
    reset_link: str,
    settings: Settings,
) -> bool:
    """Send password reset email via SMTP or log to console in dev mode.

    Args:
        to_email: Recipient email address
        first_name: User's first name for personalized greeting
        reset_link: Password reset URL with token
        settings: Application settings with SMTP config

    Returns:
        True if email sent successfully or logged (dev mode), False on error
    """
    display_name = first_name or "there"
    expiry_minutes = 10

    # Dev mode: log reset link to console
    if not is_smtp_configured(settings):
        logger.info(
            "Password reset email (dev mode)",
            extra={
                "email": to_email,
                "event": "email_dev_mode",
                "reset_link": reset_link,
            },
        )
        logger.info("=" * 60)
        logger.info("PASSWORD RESET (Dev Mode - SMTP not configured)")
        logger.info(f"  To: {to_email}")
        logger.info(f"  Link: {reset_link}")
        logger.info(f"  Expires in: {expiry_minutes} minutes")
        logger.info("=" * 60)
        return True

    # Production mode: send via SMTP
    try:
        # Render templates
        html_template = _jinja_env.get_template("password_reset.html")
        text_template = _jinja_env.get_template("password_reset.txt")

        template_vars = {
            "first_name": display_name,
            "reset_link": reset_link,
            "expiry_minutes": expiry_minutes,
        }

        html_body = html_template.render(**template_vars)
        text_body = text_template.render(**template_vars)

        # Build multipart email message
        msg = EmailMessage()
        msg["Subject"] = "Spectra - Reset Your Password"
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email

        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        # Send via SMTP
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_pass,
            start_tls=True,
        )

        logger.info(
            "Password reset email sent",
            extra={"email": to_email, "event": "email_sent"},
        )
        return True

    except Exception as e:
        logger.error(
            "Failed to send password reset email",
            extra={"email": to_email, "event": "email_failed", "error": str(e)},
        )
        return False


async def send_invite_email(
    to_email: str,
    invite_link: str,
    expiry_date: str,
    settings: Settings,
) -> bool:
    """Send invitation email via SMTP or log to console in dev mode.

    Args:
        to_email: Recipient email address
        invite_link: Invitation acceptance URL with token
        expiry_date: Human-readable expiry date string
        settings: Application settings with SMTP config

    Returns:
        True if email sent successfully or logged (dev mode), False on error
    """
    # Dev mode: log invite link to console
    if not is_smtp_configured(settings):
        logger.info(
            "Invitation email (dev mode)",
            extra={
                "email": to_email,
                "event": "email_dev_mode",
                "invite_link": invite_link,
            },
        )
        logger.info("=" * 60)
        logger.info("INVITATION (Dev Mode - SMTP not configured)")
        logger.info(f"  To: {to_email}")
        logger.info(f"  Link: {invite_link}")
        logger.info(f"  Expires: {expiry_date}")
        logger.info("=" * 60)
        return True

    # Production mode: send via SMTP
    try:
        # Render templates
        html_template = _jinja_env.get_template("invite.html")
        text_template = _jinja_env.get_template("invite.txt")

        template_vars = {
            "invite_link": invite_link,
            "expiry_date": expiry_date,
        }

        html_body = html_template.render(**template_vars)
        text_body = text_template.render(**template_vars)

        # Build multipart email message
        msg = EmailMessage()
        msg["Subject"] = "You've been invited to join Spectra"
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email

        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        # Send via SMTP
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_pass,
            start_tls=True,
        )

        logger.info(
            "Invitation email sent",
            extra={"email": to_email, "event": "email_sent"},
        )
        return True

    except Exception as e:
        logger.error(
            "Failed to send invitation email",
            extra={"email": to_email, "event": "email_failed", "error": str(e)},
        )
        return False


async def validate_smtp_connection(settings: Settings) -> bool:
    """Validate SMTP connection at application startup.

    This is a non-blocking check: if SMTP is not configured or connection
    fails, the application still starts (email falls back to dev mode).

    Returns:
        True if SMTP connection verified, False otherwise
    """
    if not is_smtp_configured(settings):
        logger.info(
            "SMTP not configured - email will use console logging (dev mode)"
        )
        return False

    try:
        smtp = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=True,
            timeout=10,
        )
        await smtp.connect()
        await smtp.login(settings.smtp_user, settings.smtp_pass)
        await smtp.quit()
        logger.info("SMTP connection validated successfully")
        return True
    except Exception as e:
        logger.warning(
            "SMTP connection validation failed - email may not work",
            extra={"error": str(e), "event": "smtp_validation_failed"},
        )
        return False
