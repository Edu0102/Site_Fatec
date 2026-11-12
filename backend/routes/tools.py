import re
from urllib.parse import urlsplit

from flask import Blueprint, jsonify, session

from auth import current_user, login_required
from repositories import tools
from routes import json_field, to_http

bp = Blueprint("tools", __name__)

NOT_FOUND = "Tool not found."


def _valid_url(url):
    """A real web address: http(s), a host made of dot-separated labels, no spaces. Blocks javascript:/data: links."""
    if not url or len(url) > 2000 or re.search(r"\s", url):
        return False
    try:
        parts = urlsplit(url)
        host = parts.hostname
        parts.port  # raises ValueError for a bad port
    except ValueError:
        return False
    return parts.scheme.lower() in ("http", "https") and bool(host) and re.fullmatch(r"[\w-]+(\.[\w-]+)*", host) is not None


def _read_tool():
    """Validated tool fields from the JSON body as (fields, None), or (None, error response)."""
    name = json_field("name").strip()
    url = json_field("url").strip()
    description = json_field("description").strip()
    category = json_field("category").strip()
    icon = json_field("icon").strip()
    if not name or len(name) > 100:
        return None, (jsonify(error="Name is required (max 100 characters)."), 400)
    if not _valid_url(url):
        return None, (jsonify(error="Enter a valid web address starting with http:// or https://."), 400)
    if len(description) > 120:
        return None, (jsonify(error="Description must have at most 120 characters."), 400)
    if len(category) > 50:
        return None, (jsonify(error="Category must have at most 50 characters."), 400)
    if not re.fullmatch(r"bi-[a-z0-9-]+", icon):
        icon = "bi-tools"
    return (name, description, url, category, icon), None


@bp.get("/tools")
@login_required
def list_tools():
    """Every tool, with the user's own usage and whether they may edit it."""
    user = current_user()
    rows = tools.get_all(user["user_id"])
    for row in rows:
        row["canEdit"] = user["user_role"] == "admin" or row["createdBy"] == user["user_id"]
    return jsonify(rows)


@bp.post("/tools")
@login_required
def create_tool():
    """Any logged-in user may add a tool."""
    fields, error = _read_tool()
    if error:
        return error
    return jsonify(message="Tool created.", id=tools.add(session["user_id"], *fields))


@bp.put("/tools/<int:tool_id>")
@login_required
def update_tool(tool_id):
    """Only the creator or an admin may change a tool."""
    fields, error = _read_tool()
    if error:
        return error
    result = tools.update(tool_id, session["user_id"], current_user()["user_role"], *fields)
    return to_http(result, "Tool updated.", NOT_FOUND)


@bp.delete("/tools/<int:tool_id>")
@login_required
def delete_tool(tool_id):
    """Only the creator or an admin may delete a tool."""
    return to_http(tools.delete(tool_id, session["user_id"], current_user()["user_role"]), "Tool deleted.", NOT_FOUND)


@bp.post("/tools/<int:tool_id>/open")
@login_required
def open_tool(tool_id):
    """Record that the user opened the tool (feeds "Recentes")."""
    return to_http(tools.record_open(tool_id, session["user_id"]), "Open recorded.", NOT_FOUND)
