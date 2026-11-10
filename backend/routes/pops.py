from flask import Blueprint, jsonify, session

from auth import current_user, login_required, role_required
from repositories import pops
from routes import POP_UNAVAILABLE, json_field

bp = Blueprint("pops", __name__)
STATUSES = ("draft", "published", "archived")
NOT_FOUND = {"error": "POP not found."}


def _pop_fields(default_status):
    """Validated POP fields from the JSON body, or an error response tuple."""
    title = json_field("title").strip()
    if not title:
        return None, (jsonify(error="Title is required."), 400)
    status = json_field("status").strip().lower() or default_status
    if status not in STATUSES:
        return None, (jsonify(error="Status must be draft, published or archived."), 400)
    optional = [json_field(k).strip() or None for k in ("description", "filePath", "version")]
    return (title, *optional, status), None


@bp.get("/pops")
@login_required
def list_pops():
    """POPs this user may see (admins: all)."""
    return jsonify(pops.list_visible(session["user_id"], current_user()["user_role"]))


@bp.get("/pops/<int:pop_id>")
@login_required
def get_pop(pop_id):
    """One POP, if this user may see it."""
    pop = pops.get_visible_dict(pop_id, session["user_id"], current_user()["user_role"])
    return (jsonify(pop), 200) if pop else (jsonify(POP_UNAVAILABLE), 404)


@bp.post("/pops")
@role_required("admin")
def create_pop():
    """Admins create a POP; status defaults to draft."""
    fields, error = _pop_fields("draft")
    if error:
        return error
    return jsonify(message="POP created.", id=pops.add(session["user_id"], *fields))


@bp.put("/pops/<int:pop_id>")
@role_required("admin")
def update_pop(pop_id):
    """Admins replace a POP's fields; status is required."""
    fields, error = _pop_fields(None)
    if error:
        return error
    if not pops.update(session["user_id"], pop_id, *fields):
        return jsonify(NOT_FOUND), 404
    return jsonify(message="POP updated.")


@bp.post("/pops/<int:pop_id>/archive")
@role_required("admin")
def archive_pop(pop_id):
    """Admins archive a POP (POPs are never deleted)."""
    if not pops.archive(session["user_id"], pop_id):
        return jsonify(NOT_FOUND), 404
    return jsonify(message="POP archived.")
