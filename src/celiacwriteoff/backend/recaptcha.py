"""Verification of Google reCAPTCHA v2 tokens on signup/login."""

import os

import httpx
from dotenv import load_dotenv

SITEVERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def verify_recaptcha(token: str, remote_ip: str | None = None) -> bool:
    """Check a reCAPTCHA token against Google's siteverify API.

    If RECAPTCHA_SECRET_KEY is unset, verification is skipped (returns True).
    This is a local dev/test escape hatch only -- a real CAPTCHA can't be
    solved by curl or automated tests. Never leave the key unset in production.
    """
    load_dotenv()
    secret = os.getenv("RECAPTCHA_SECRET_KEY")
    if not secret:
        return True
    if not token:
        return False

    data = {"secret": secret, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        response = httpx.post(SITEVERIFY_URL, data=data, timeout=5.0)
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError):
        return False

    return bool(result.get("success"))
