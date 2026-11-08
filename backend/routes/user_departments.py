from flask import Blueprint, jsonify, session

from auth import login_required, role_required
from repositories import user_departments
from routes import json_field, json_int, to_http

bp = Blueprint("user_departments", __name__)


@bp.post("/user-departments")
@role_required("admin")
def assign_user():
    """Admins add a user to a department; accessType defaults to "member"."""
    user_id, department_id = json_int("userId"), json_int("departmentId")
    if user_id is None or department_id is None:
        return jsonify(error="User id and department id must be whole numbers."), 400
    access_type = json_field("accessType").strip() or "member"
    return to_http(user_departments.assign(user_id, department_id, access_type), "User assigned to department.",
                   "User or department not found.", "This user is already assigned to the department.")


@bp.get("/me/departments")
@login_required
def my_departments():
    """The logged-in user's current departments."""
    return jsonify(user_departments.list_for_user(session["user_id"]))
