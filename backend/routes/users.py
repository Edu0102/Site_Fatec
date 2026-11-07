from flask import Blueprint, jsonify

from auth import login_required, role_required
from repositories import users

bp = Blueprint("users", __name__)


@bp.get("/users")
@login_required
def list_users():
    """Names of all active users."""
    return jsonify(users.active_names())


@bp.get("/admin-only")
@role_required("admin")
def admin_only():
    """Sample admin-only endpoint."""
    return jsonify(secret="admins only")
