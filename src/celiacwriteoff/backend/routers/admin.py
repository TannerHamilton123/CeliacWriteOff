import sqlite3
from typing import Annotated

import db
from auth import CurrentUserDep
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas import LoginAttemptsPage

router = APIRouter(prefix="/admin", tags=["admin"])

DBDep = Annotated[sqlite3.Connection, Depends(db.get_db)]


def require_admin(current_user: CurrentUserDep) -> sqlite3.Row:
    if not current_user["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


AdminDep = Annotated[sqlite3.Row, Depends(require_admin)]


@router.get("/login-attempts")
def get_login_attempts(
    admin: AdminDep,
    conn: DBDep,
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    email: str | None = None,
) -> LoginAttemptsPage:
    attempts = db.list_login_attempts(conn, limit, offset, email)
    total = db.count_login_attempts(conn, email)
    return {"attempts": [dict(row) for row in attempts], "total": total}
