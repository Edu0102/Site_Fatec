import re

from flask import Blueprint, jsonify

from auth import login_required, role_required
from repositories import phones
from routes import json_body, json_field, json_int, json_tags

bp = Blueprint("phones", __name__)

NOT_FOUND = "Contact not found."


def _error(message):
    """(None, 400 response) for _read_contact."""
    return None, (jsonify(error=message), 400)


def _read_contact():
    """Validated contact fields from the JSON body as (fields, None), or (None, error response)."""
    name = json_field("name").strip()
    extension = json_field("extension").strip()
    phone_number = json_field("phoneNumber").strip()
    email = json_field("email").strip()
    tag_names = json_tags()
    department_id = None
    if json_body().get("departmentId") is not None:
        department_id = json_int("departmentId")
        if department_id is None:
            return _error("Department id must be a whole number.")
    if not name or len(name) > 100:
        return _error("Name is required (max 100 characters).")
    if len(extension) > 20 or len(phone_number) > 30:
        return _error("Extension and phone number must have at most 20 and 30 characters.")
    if email and (len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)):
        return _error("Enter a valid email address.")
    if tag_names is None:
        return _error("Tags must be a list of names up to 40 characters (max 20).")
    return (name, department_id, extension, phone_number, email, tag_names), None


@bp.get("/phones")
@login_required
def list_phones():
    """All contacts, for everyone logged in."""
    return jsonify(phones.get_all())


@bp.post("/phones")
@role_required("admin")
def create_phone():
    """Admins add a contact."""
    fields, error = _read_contact()
    if error:
        return error
    result = phones.add(*fields)
    if result == "bad_department":
        return jsonify(error="Department not found."), 400
    return jsonify(message="Contact created.", id=result)


@bp.put("/phones/<int:phone_id>")
@role_required("admin")
def update_phone(phone_id):
    """Admins change a contact and its filters."""
    fields, error = _read_contact()
    if error:
        return error
    result = phones.update(phone_id, *fields)
    if result == "bad_department":
        return jsonify(error="Department not found."), 400
    if result == "not_found":
        return jsonify(error=NOT_FOUND), 404
    return jsonify(message="Contact updated.")


@bp.delete("/phones/<int:phone_id>")
@role_required("admin")
def delete_phone(phone_id):
    """Admins delete a contact; it also leaves the POPs that used it."""
    if not phones.delete(phone_id):
        return jsonify(error=NOT_FOUND), 404
    return jsonify(message="Contact deleted.")
