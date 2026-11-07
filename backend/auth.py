from functools import wraps

from flask import g, jsonify, session

from repositories import users

NOT_AUTHENTICATED = {"error": "Not authenticated."}
FORBIDDEN = {"error": "Forbidden."}


def current_user():
    """The logged-in user's row from the database (cached per request); None if the session is not valid."""
    if "current_user" not in g:
        user = users.get_by_id(session["user_id"]) if "user_id" in session else None
        valid = user is not None and user["is_active"] == 1 and session.get("sv") == user["user_session_version"]
        g.current_user = user if valid else None
    return g.current_user


def login_required(view):
    """Answer 401 JSON unless the session belongs to an active user with the current session version."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            session.clear()
            return jsonify(NOT_AUTHENTICATED), 401
        return view(*args, **kwargs)
    return wrapper


def role_required(role):
    """Answer 401 if not logged in, 403 if the user's role in the database is not `role`."""
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(*args, **kwargs):
            if current_user()["user_role"] != role:
                return jsonify(FORBIDDEN), 403
            return view(*args, **kwargs)
        return wrapper
    return decorator
