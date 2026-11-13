from flask import Blueprint, jsonify

from auth import login_required, role_required
from repositories import tags
from routes import json_field

bp = Blueprint("tags", __name__)


@bp.get("/tags/<any(link, phone):scope>")
@login_required
def list_tags(scope):
    """A page's filters, for everyone."""
    return jsonify(tags.get_all(scope))


@bp.post("/tags/<any(link, phone):scope>")
@role_required("admin")
def create_tag(scope):
    """Admins add a filter to a page."""
    name = json_field("name").strip()
    if not name or len(name) > 40:
        return jsonify(error="Filter name is required (max 40 characters)."), 400
    tag_id = tags.add(scope, name)
    if tag_id == "conflict":
        return jsonify(error="This filter already exists."), 409
    return jsonify(message="Filter created.", id=tag_id)


@bp.delete("/tags/<int:tag_id>")
@role_required("admin")
def delete_tag(tag_id):
    """Admins remove a filter; items keep everything else."""
    if not tags.delete(tag_id):
        return jsonify(error="Filter not found."), 404
    return jsonify(message="Filter deleted.")
