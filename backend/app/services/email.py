"""Email service for sending password reset and other emails."""

import logging
from typing import Optional

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

_DEV_PLACEHOLDERS = {"", "dev-api-key", "your-email-api-key", "changeme"}


async def send_password_reset_email(
    to_email: str,
    reset_link: str,
    settings: Settings
) -> bool:
    """Send password reset email via email service.

    In development mode (no EMAIL_SERVICE_API_KEY configured), this logs
    the reset link to the console instead of sending an email.

    Args:
        to_email: Recipient email address
        reset_link: Password reset URL with token
        settings: Application settings

    Returns:
        True if email sent successfully or logged (dev mode), False otherwise
    """
    # Development mode: log reset link instead of sending email
    if not settings.email_service_api_key or settings.email_service_api_key.strip() in _DEV_PLACEHOLDERS:
        logger.info("=" * 80)
        logger.info("PASSWORD RESET REQUEST (Development Mode)")
        logger.info(f"To: {to_email}")
        logger.info(f"Reset Link: {reset_link}")
        logger.info("Link expires in 10 minutes")
        logger.info("=" * 80)
        return True

    # Production mode: send via Mailgun API
    try:
        async with httpx.AsyncClient() as client:
            # Mailgun API endpoint (assumes using US region)
            # Extract domain from email_from
            domain = settings.email_from.split("@")[-1]
            url = f"https://api.mailgun.net/v3/{domain}/messages"

            # Prepare email content
            subject = "Spectra - Password Reset Request"
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>Password Reset Request</h2>
                <p>You requested to reset your password for your Spectra account.</p>
                <p>Click the link below to reset your password:</p>
                <p>
                    <a href="{reset_link}"
                       style="display: inline-block; padding: 10px 20px;
                              background-color: #007bff; color: white;
                              text-decoration: none; border-radius: 5px;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all;">{reset_link}</p>
                <p><strong>This link will expire in 10 minutes.</strong></p>
                <p>If you did not request this password reset, please ignore this email.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    This is an automated email from Spectra. Please do not reply.
                </p>
            </body>
            </html>
            """

            # Send email via Mailgun
            response = await client.post(
                url,
                auth=("api", settings.email_service_api_key),
                data={
                    "from": settings.email_from,
                    "to": to_email,
                    "subject": subject,
                    "html": html_body,
                }
            )

            if response.status_code == 200:
                logger.info(f"Password reset email sent to {to_email}")
                return True
            else:
                logger.error(
                    f"Failed to send email: {response.status_code} - {response.text}"
                )
                return False

    except Exception as e:
        logger.error(f"Error sending password reset email: {e}")
        return False
