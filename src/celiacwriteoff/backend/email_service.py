"""Password reset email delivery via SendGrid."""

import os

from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    """Send a password reset link.

    If SENDGRID_API_KEY or RESET_EMAIL_FROM is unset, the link is logged to
    the console instead of sent -- a local dev/test fallback so the reset
    flow is testable without a real SendGrid account.
    """
    load_dotenv()
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("RESET_EMAIL_FROM")
    if not api_key or not from_email:
        print(f"[email_service] SendGrid not configured; reset link for {to_email}: {reset_url}")
        return

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject="Reset your CeliacWriteOff password",
        plain_text_content=(
            f"We received a request to reset your password.\n\n"
            f"Reset it here: {reset_url}\n\n"
            f"This link expires in 45 minutes. If you didn't request this, "
            f"you can ignore this email."
        ),
    )
    try:
        SendGridAPIClient(api_key).send(message)
    except Exception:
        # Don't let a SendGrid outage break the enumeration-safe response
        # from /auth/forgot-password -- the caller always returns success.
        print(f"[email_service] Failed to send reset email to {to_email}")
