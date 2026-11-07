from flask import Blueprint, jsonify, session

from auth import current_user, login_required
from repositories import pops, standard_checks
from routes import POP_UNAVAILABLE, json_field, json_int, to_http

bp = Blueprint("standard_checks", __name__)


@bp.get("/pops/<int:pop_id>/standard-checks")
@login_required
def list_standard_checks(pop_id):
    """A POP's standard checks, if the user may see the POP."""
    if pops.get_visible(pop_id, session["user_id"], current_user()["user_role"]) is None:
        return jsonify(POP_UNAVAILABLE), 404
    return jsonify(standard_checks.list_for_pop(pop_id))


@bp.post("/pops/<int:pop_id>/standard-checks")
@login_required
def create_standard_check(pop_id):
    """Add a standard check to a POP; the admin check is done against the database."""
    check_text, check_order = json_field("checkText").strip(), json_int("checkOrder")
    if not check_text:
        return jsonify(error="Check text is required."), 400
    if check_order is None:
        return jsonify(error="Check order must be a whole number."), 400
    result, new_id = standard_checks.add(session["user_id"], pop_id, check_text, check_order)
    body, status = to_http(result, "Standard check created.", "POP not found.")
    if result == "ok":
        body["id"] = new_id
    return body, status
