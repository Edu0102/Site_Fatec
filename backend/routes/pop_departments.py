from flask import Blueprint, jsonify, session

from auth import current_user, login_required, role_required
from repositories import pop_departments, pops
from routes import POP_UNAVAILABLE, json_field, json_int, to_http

bp = Blueprint("pop_departments", __name__)


@bp.get("/pops/<int:pop_id>/departments")
@login_required
def list_pop_departments(pop_id):
    """Departments a POP is shared with, for anyone who can see the POP."""
    if pops.get_visible(pop_id, session["user_id"], current_user()["user_role"]) is None:
        return jsonify(POP_UNAVAILABLE), 404
    return jsonify(pop_departments.list_for_pop(pop_id))


@bp.post("/pop-departments")
@role_required("admin")
def share_pop():
    """Admins share a POP with a department; accessType defaults to "read" (stored, not used by any rule)."""
    pop_id, department_id = json_int("popId"), json_int("departmentId")
    if pop_id is None or department_id is None:
        return jsonify(error="POP id and department id must be whole numbers."), 400
    access_type = json_field("accessType").strip() or "read"
    return to_http(pop_departments.assign(pop_id, department_id, access_type), "Department assigned to POP.",
                   "POP or department not found.", "This department is already assigned to the POP.")


@bp.delete("/pops/<int:pop_id>/departments/<int:department_id>")
@role_required("admin")
def unshare_pop(pop_id, department_id):
    """Admins stop sharing a POP with a department."""
    if not pop_departments.remove(pop_id, department_id):
        return jsonify(error="This department is not assigned to this POP."), 404
    return jsonify(message="Department removed from POP.")
