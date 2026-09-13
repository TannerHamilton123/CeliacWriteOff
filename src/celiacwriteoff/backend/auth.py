import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
import db
from fastapi import Cookie, Depends, HTTPException, Response

SESSION_COOKIE_NAME = "session_token"
SESSION_TTL = timedelta(days=30)
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def start_session(conn: sqlite3.Connection, response: Response, user_id: str) -> None:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + SESSION_TTL
    db.create_session(conn, token, user_id, expires_at.isoformat())
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=int(SESSION_TTL.total_seconds()),
    )


def end_session(conn: sqlite3.Connection, response: Response, token: str | None) -> None:
    if token:
        db.delete_session(conn, token)
    response.delete_cookie(SESSION_COOKIE_NAME)


def get_current_user(
    conn: Annotated[sqlite3.Connection, Depends(db.get_db)],
    session_token: Annotated[str | None, Cookie()] = None,
) -> sqlite3.Row:
    if session_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.get_session_user(conn, session_token)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


CurrentUserDep = Annotated[sqlite3.Row, Depends(get_current_user)]
