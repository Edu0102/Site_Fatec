from flask import Blueprint, jsonify, session

from auth import login_required, role_required
from repositories import departments
from routes import json_bool, json_field, to_http

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


@bp.put("/departments/<int:department_id>")
@role_required("admin")
def update_department(department_id):
    """Admins rename, recode or (de)activate a department; inactive departments stop granting POP access."""
    name, code, is_active = json_field("name").strip(), json_field("code").strip().upper(), json_bool("isActive")
    if not name or not code:
        return jsonify(error="Name and code are required."), 400
    if is_active is None:
        return jsonify(error="isActive must be true or false."), 400
    return to_http(departments.update(department_id, name, code, is_active), "Department updated.",
                   "Department not found.", "This department code already exists.")
