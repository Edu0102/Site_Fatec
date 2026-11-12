import re
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, session

from auth import login_required, role_required
from repositories import user_departments
from routes import json_body, json_field, json_int, to_http

bp = Blueprint("user_departments", __name__)

BAD_DATE = {"error": "Dates must be YYYY-MM-DD."}


def _sp_day_start(day):
    """São Paulo midnight of a date as UTC text (the portal only runs in SP: fixed UTC-3, no DST since 2019)."""
    return f"{day.isoformat()}T03:00:00.000000Z"


def _read_date(name):
    """(date or None, ok): None when the field is absent; ok is False when present but not a real YYYY-MM-DD."""
    if name not in json_body():
        return None, True
    text = json_field(name)
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):  # fromisoformat also takes "2026-W45-3" etc.
            raise ValueError
        day = date.fromisoformat(text)
        if day >= date.max:  # the end date gets a day added
            raise ValueError
        return day, True
    except ValueError:
        return None, False


@bp.post("/user-departments")
@role_required("admin")
def assign_user():
    """Admins add a user to a department; accessType defaults to "member"."""
    user_id, department_id = json_int("userId"), json_int("departmentId")
    if user_id is None or department_id is None:
        return jsonify(error="User id and department id must be whole numbers."), 400
    access_type = json_field("accessType").strip() or "member"
    start, ok_start = _read_date("validFrom")
    end, ok_end = _read_date("expiresAt")
    if not (ok_start and ok_end):
        return jsonify(BAD_DATE), 400
    if start and end and end < start:
        return jsonify(error="The end date can't be before the start date."), 400
    if end and end < datetime.now(timezone(timedelta(hours=-3))).date():
        return jsonify(error="The end date can't be in the past."), 400
    valid_from = _sp_day_start(start) if start else None
    # The end date counts as a whole São Paulo day: access ends just before the next day starts
    expires_at = f"{(end + timedelta(days=1)).isoformat()}T02:59:59.999999Z" if end else None
    return to_http(user_departments.assign(user_id, department_id, access_type, valid_from, expires_at), "User assigned to department.",
                   "User or department not found.", "This user is already assigned to the department.")


@bp.get("/me/departments")
@login_required
def my_departments():
    """The logged-in user's current departments."""
    return jsonify(user_departments.list_for_user(session["user_id"]))


@bp.get("/me/colleagues")
@login_required
def my_colleagues():
    """The logged-in user's departments and who is in them (what collaborators see on the Colaboradores page)."""
    return jsonify(user_departments.colleagues(session["user_id"]))


@bp.get("/departments/<int:department_id>/members")
@role_required("admin")
def department_members(department_id):
    """Admins see who is currently in a department."""
    return jsonify(user_departments.members(department_id))


@bp.delete("/departments/<int:department_id>/members/<int:user_id>")
@role_required("admin")
def remove_member(department_id, user_id):
    """Admins take someone out of a department; they lose its POPs at once."""
    if not user_departments.remove(user_id, department_id):
        return jsonify(error="This user is not in the department."), 404
    return jsonify(message="User removed from department.")
