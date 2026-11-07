from functools import wraps

from flask import jsonify, session

NOT_AUTHENTICATED = {"error": "Not authenticated."}
FORBIDDEN = {"error": "Forbidden."}


def login_required(view):
    """Answer 401 JSON unless someone is logged in."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(NOT_AUTHENTICATED), 401
        return view(*args, **kwargs)
    return wrapper


def role_required(role):
    """Answer 401 if not logged in, 403 if the session role is not `role`."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return jsonify(NOT_AUTHENTICATED), 401
            if session.get("role") != role:
                return jsonify(FORBIDDEN), 403
            return view(*args, **kwargs)
        return wrapper
    return decorator
