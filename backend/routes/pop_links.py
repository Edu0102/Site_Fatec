from flask import Blueprint, jsonify, session

from auth import current_user, login_required, role_required
from repositories import pop_links, pops
from routes import POP_UNAVAILABLE, json_int, to_http

bp = Blueprint("pop_links", __name__)


@bp.get("/pops/<int:pop_id>/links")
@login_required
def list_pop_links(pop_id):
    """Links a POP has, for anyone who can see the POP."""
    if pops.get_visible(pop_id, session["user_id"], current_user()["user_role"]) is None:
        return jsonify(POP_UNAVAILABLE), 404
    return jsonify(pop_links.list_for_pop(pop_id))


@bp.post("/pop-links")
@role_required("admin")
def assign_link():
    """Admins assign a link to a POP."""
    pop_id, link_id = json_int("popId"), json_int("linkId")
    if pop_id is None or link_id is None:
        return jsonify(error="POP id and link id must be whole numbers."), 400
    return to_http(pop_links.assign(pop_id, link_id), "Link assigned to POP.", "POP or link not found.",
                   "This link is already assigned to the POP.")


@bp.delete("/pops/<int:pop_id>/links/<int:link_id>")
@role_required("admin")
def unassign_link(pop_id, link_id):
    """Admins remove a link from a POP."""
    if not pop_links.remove(pop_id, link_id):
        return jsonify(error="This link is not assigned to this POP."), 404
    return jsonify(message="Link removed from POP.")
