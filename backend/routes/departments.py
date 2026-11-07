from flask import Blueprint, jsonify, session

from auth import login_required
from repositories import departments
from routes import json_field, to_http

bp = Blueprint("departments", __name__)


@bp.get("/departments")
@login_required
def list_departments():
    """All departments, for any logged-in user."""
    return jsonify(departments.get_all())


@bp.post("/departments")
@login_required
def create_department():
    """Create a department; the admin check is done against the database."""
    name, code = json_field("name"), json_field("code")
    if not name.strip() or not code.strip():
        return jsonify(error="Name and code are required."), 400
    result = departments.add(session["user_id"], name.strip(), code.strip().upper())
    return to_http(result, "Department created.", "Department not found.", "This department code already exists.")
