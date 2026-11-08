from flask import Blueprint, jsonify, session

from auth import current_user, login_required, role_required
from repositories import phones, pop_phones, pops
from routes import POP_UNAVAILABLE, json_int, to_http

bp = Blueprint("pop_phones", __name__)


@bp.get("/pops/<int:pop_id>/phones")
@login_required
def list_pop_phones(pop_id):
    """The phone numbers of a POP, if this user may see the POP."""
    if pops.get_visible(pop_id, session["user_id"], current_user()["user_role"]) is None:
        return jsonify(POP_UNAVAILABLE), 404
    return jsonify(phones.get_for_pop(pop_id))


@bp.post("/pop-phones")
@role_required("admin")
def assign_phone():
    """Assign a phone number to a POP."""
    pop_id, phone_id = json_int("popId"), json_int("phoneId")
    if pop_id is None or phone_id is None:
        return jsonify(error="POP id and phone id must be whole numbers."), 400
    return to_http(pop_phones.add(pop_id, phone_id), "Phone number assigned to POP.",
                   "POP or phone number not found.", "This phone number is already assigned to the POP.")


@bp.delete("/pops/<int:pop_id>/phones/<int:phone_id>")
@role_required("admin")
def remove_phone(pop_id, phone_id):
    """Unassign a phone number from a POP."""
    if not pop_phones.remove(pop_id, phone_id):
        return jsonify(error="This phone number is not assigned to this POP."), 404
    return jsonify(message="Phone number removed from POP.")
