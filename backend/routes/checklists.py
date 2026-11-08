from flask import Blueprint, jsonify, session

from auth import current_user, login_required
from repositories import checklists, pops
from routes import POP_UNAVAILABLE, json_bool, json_field, to_http

bp = Blueprint("checklists", __name__)
NOT_FOUND = {"error": "Checklist not found."}
COMPLETED = "This checklist is already completed."


@bp.post("/pops/<int:pop_id>/checklists")
@login_required
def create_checklist(pop_id):
    """Start a checklist on a POP the user can see."""
    if pops.get_visible(pop_id, session["user_id"], current_user()["user_role"]) is None:
        return jsonify(POP_UNAVAILABLE), 404
    description = json_field("description").strip() or None
    new_id = checklists.create(pop_id, session["user_id"], description)
    return jsonify(message="Checklist created.", id=new_id)


@bp.get("/checklists/<int:checklist_id>")
@login_required
def get_checklist(checklist_id):
    """One checklist with items; only its owner or an admin may read it."""
    checklist = checklists.get(checklist_id)
    if checklist is None or (checklist["userId"] != session["user_id"] and current_user()["user_role"] != "admin"):
        return jsonify(NOT_FOUND), 404
    return jsonify(checklist)


@bp.get("/me/checklists")
@login_required
def my_checklists():
    """The logged-in user's checklists."""
    return jsonify(checklists.list_for_user(session["user_id"]))


@bp.put("/checklists/<int:checklist_id>/items/<int:standard_check_id>")
@login_required
def set_item(checklist_id, standard_check_id):
    """Tick or untick one item of the user's own open checklist."""
    is_checked = json_bool("isChecked")
    if is_checked is None:
        return jsonify(error="isChecked must be true or false."), 400
    result = checklists.set_item(session["user_id"], checklist_id, standard_check_id, is_checked)
    return to_http(result, "Checklist item updated.", "Checklist item not found.", COMPLETED)


@bp.post("/checklists/<int:checklist_id>/complete")
@login_required
def complete_checklist(checklist_id):
    """Mark the user's own checklist as completed."""
    return to_http(checklists.complete(session["user_id"], checklist_id), "Checklist completed.", "Checklist not found.", COMPLETED)


@bp.delete("/checklists/<int:checklist_id>")
@login_required
def delete_checklist(checklist_id):
    """The owner throws away a checklist that is not completed yet."""
    return to_http(checklists.delete(session["user_id"], checklist_id), "Checklist deleted.", "Checklist not found.", COMPLETED)
