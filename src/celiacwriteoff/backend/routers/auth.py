import sqlite3
from typing import Annotated

import db
from auth import CurrentUserDep, end_session, hash_password, start_session, verify_password
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from schemas import UserCreate, UserLogin, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

DBDep = Annotated[sqlite3.Connection, Depends(db.get_db)]


@router.post("/signup", status_code=201)
def signup(payload: UserCreate, response: Response, conn: DBDep) -> UserOut:
    if db.get_user_by_email(conn, payload.email) is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")
    user_id = db.create_user(conn, payload.email, hash_password(payload.password))
    start_session(conn, response, user_id)
    return dict(db.get_user_by_id(conn, user_id))


@router.post("/login")
def login(payload: UserLogin, response: Response, conn: DBDep) -> UserOut:
    user = db.get_user_by_email(conn, payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
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
