from flask import Blueprint, jsonify

from auth import login_required, role_required
from repositories import links
from routes import json_field, json_tags, to_http, valid_url

bp = Blueprint("links", __name__)

NOT_FOUND = "Link not found."
CONFLICT = "A link with this address already exists."


def _read_link():
    """Validated link fields from the JSON body as (fields, None), or (None, error response)."""
    title = json_field("title").strip()
    url = json_field("url").strip()
    description = json_field("description").strip()
    subject = json_field("subject").strip()
    tag_names = json_tags()
    if not title or len(title) > 150:
        return None, (jsonify(error="Title is required (max 150 characters)."), 400)
    if not valid_url(url):
        return None, (jsonify(error="Enter a valid web address starting with http:// or https://."), 400)
    if len(description) > 500:
        return None, (jsonify(error="Description must have at most 500 characters."), 400)
    if len(subject) > 100:
        return None, (jsonify(error="Subject must have at most 100 characters."), 400)
    if tag_names is None:
        return None, (jsonify(error="Tags must be a list of names up to 40 characters (max 20)."), 400)
    return (title, description, url, subject, tag_names), None


@bp.get("/links")
@login_required
def list_links():
    """All links, for everyone logged in."""
    return jsonify(links.get_all())


@bp.post("/links")
@role_required("admin")
def create_link():
    """Admins add a link; a URL already in use is refused."""
    fields, error = _read_link()
    if error:
        return error
    link_id = links.add(*fields)
    if link_id == "conflict":
        return jsonify(error=CONFLICT), 409
    return jsonify(message="Link created.", id=link_id)


@bp.put("/links/<int:link_id>")
@role_required("admin")
def update_link(link_id):
    """Admins change a link and its filters."""
    fields, error = _read_link()
    if error:
        return error
    return to_http(links.update(link_id, *fields), "Link updated.", NOT_FOUND, CONFLICT)


@bp.delete("/links/<int:link_id>")
@role_required("admin")
def delete_link(link_id):
    """Admins delete a link; it also leaves the POPs that used it."""
    if not links.delete(link_id):
        return jsonify(error=NOT_FOUND), 404
    return jsonify(message="Link deleted.")
