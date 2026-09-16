import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Annotated

import db
from auth import CurrentUserDep, end_session, hash_password, start_session, verify_password
from email_service import send_password_reset_email
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from recaptcha import verify_recaptcha
from schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserLogin,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

DBDep = Annotated[sqlite3.Connection, Depends(db.get_db)]

RESET_TOKEN_TTL = timedelta(minutes=45)


def _frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173")


@router.post("/signup", status_code=201)
def signup(payload: UserCreate, request: Request, response: Response, conn: DBDep) -> UserOut:
    if not verify_recaptcha(payload.recaptcha_token, request.client.host if request.client else None):
        raise HTTPException(status_code=400, detail="CAPTCHA verification failed")
    if db.get_user_by_email(conn, payload.email) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user_id = db.create_user(conn, payload.email, hash_password(payload.password), payload.full_name)
    start_session(conn, response, user_id)
    return dict(db.get_user_by_id(conn, user_id))


@router.post("/login")
def login(payload: UserLogin, request: Request, response: Response, conn: DBDep) -> UserOut:
    if not verify_recaptcha(payload.recaptcha_token, request.client.host if request.client else None):
        raise HTTPException(status_code=400, detail="CAPTCHA verification failed")

    user = db.get_user_by_email(conn, payload.email)
    ok = user is not None and verify_password(payload.password, user["password_hash"])
    db.record_login_attempt(
        conn,
        email=payload.email,
        user_id=user["id"] if user else None,
        success=ok,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    if not ok:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    start_session(conn, response, user["id"])
    return dict(user)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    conn: DBDep,
    session_token: Annotated[str | None, Cookie()] = None,
) -> None:
    end_session(conn, response, session_token)


@router.get("/me")
def me(current_user: CurrentUserDep) -> UserOut:
    return dict(current_user)


@router.post("/forgot-password", status_code=200)
def forgot_password(payload: ForgotPasswordRequest, conn: DBDep) -> dict:
    user = db.get_user_by_email(conn, payload.email)
    if user is not None:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + RESET_TOKEN_TTL
        db.create_reset_token(conn, token, user["id"], expires_at.isoformat())
        reset_url = f"{_frontend_url()}/reset-password?token={token}"
        send_password_reset_email(user["email"], reset_url)
    # Same response whether or not the email is registered, to avoid enumeration.
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=200)
def reset_password(payload: ResetPasswordRequest, conn: DBDep) -> dict:
    token_row = db.get_valid_reset_token(conn, payload.token)
    if token_row is None:
        raise HTTPException(status_code=400, detail="Reset link is invalid or has expired")
    db.set_user_password(conn, token_row["user_id"], hash_password(payload.new_password))
    db.consume_reset_token(conn, payload.token)
    db.delete_sessions_for_user(conn, token_row["user_id"])
    return {"message": "Password has been reset. Please log in again."}
