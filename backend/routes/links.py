from flask import Blueprint, jsonify

from auth import role_required
from repositories import links
from routes import json_field, to_http

bp = Blueprint("links", __name__)


@bp.get("/links")
@role_required("admin")
def list_links():
    """All links, for admins."""
    return jsonify(links.get_all())


@bp.post("/links")
@role_required("admin")
def create_link():
    """Add a link path; a path already in use is refused."""
    path = json_field("path").strip()
    if not path:
        return jsonify(error="Path is required."), 400
    link_id = links.add(path)
    if link_id == "conflict":
        return jsonify(error="This link path already exists."), 409
    return jsonify(message="Link created.", id=link_id)


@bp.put("/links/<int:link_id>")
@role_required("admin")
def update_link(link_id):
    """Change a link's path."""
    path = json_field("path").strip()
    if not path:
        return jsonify(error="Path is required."), 400
    return to_http(links.update(link_id, path), "Link updated.", "Link not found.",
                   "Another link already has this path.")
