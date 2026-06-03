from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Callable

import bcrypt
from flask import g, jsonify, request

from database import create_session, create_user, delete_session, fetch_session, fetch_user_by_email, fetch_user_by_id

VALID_ROLES = {"admin", "recruiter", "student"}
SESSION_DAYS = 7


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def register_user(name: str, email: str, password: str, role: str = "recruiter") -> dict:
    role = role if role in VALID_ROLES else "recruiter"
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    user_id = create_user(name.strip(), email.strip().lower(), hash_password(password), role)
    user = fetch_user_by_id(user_id)
    if not user:
        raise ValueError("User registration failed.")
    return user


def login_user(email: str, password: str) -> tuple[dict, str, datetime]:
    user = fetch_user_by_email(email)
    if not user or not user.get("password_hash") or not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid email or password.")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    create_session(int(user["id"]), token, expires_at.isoformat())
    public_user = fetch_user_by_id(int(user["id"]))
    if not public_user:
        raise ValueError("Login failed.")
    return public_user, token, expires_at


def logout_user(token: str | None) -> None:
    if token:
        delete_session(token)


def current_user_from_request() -> dict | None:
    token = request.cookies.get("session_token") or _bearer_token()
    if not token:
        return None
    session = fetch_session(token)
    if not session:
        return None
    expires_at = datetime.fromisoformat(session["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        delete_session(token)
        return None
    return {
        "id": session["user_id"],
        "name": session["name"],
        "email": session["email"],
        "role": session["role"],
        "token": token,
    }


def require_auth(*roles: str):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user_from_request()
            if not user:
                return jsonify({"error": "Authentication required."}), 401
            if roles and user["role"] not in roles:
                return jsonify({"error": "You do not have permission for this action."}), 403
            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def _bearer_token() -> str | None:
    value = request.headers.get("Authorization", "")
    if value.lower().startswith("bearer "):
        return value.split(" ", 1)[1].strip()
    return None
