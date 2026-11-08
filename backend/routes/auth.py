from flask import Blueprint, jsonify, session

from auth import NOT_AUTHENTICATED, current_user, login_required
from repositories import users
from routes import json_field
from security import verify_password

bp = Blueprint("auth", __name__)


@bp.post("/auth/login")
def login():
    """Start a session; every failure gives the same 401."""
    user = users.get_by_email(json_field("email").strip().lower())
    if user is None or user["is_active"] != 1 or not verify_password(json_field("password"), user["user_password_hash"]):
        return jsonify(NOT_AUTHENTICATED), 401
    session.clear()
    session.permanent = True
    session.update(user_id=user["user_id"], sv=user["user_session_version"])
    return jsonify(message="Logged in.")


@bp.post("/auth/logout")
def logout():
    """End the session and invalidate copies of the cookie (works even when not logged in)."""
    if current_user() is not None:
        users.bump_session_version(session["user_id"])
    session.clear()
    return jsonify(message="Logged out.")


@bp.get("/auth/me")
@login_required
def me():
    """Who is logged in, from the session cookie."""
    user = current_user()
    return jsonify(id=user["user_id"], name=user["user_name"] or "", email=user["user_email"] or "",
                   role=user["user_role"] or "user")
