from flask import Blueprint, jsonify

from auth import role_required
from repositories import phones
from routes import json_field, to_http

bp = Blueprint("phones", __name__)


@bp.get("/phones")
@role_required("admin")
def list_phones():
    """All phone numbers (admins only)."""
    return jsonify(phones.get_all())


@bp.post("/phones")
@role_required("admin")
def create_phone():
    """Add a phone number; it must be unique."""
    number = json_field("phoneNumber").strip()
    if not number:
        return jsonify(error="Phone number is required."), 400
    result = phones.add(number)
    if result == "conflict":
        return jsonify(error="This phone number already exists."), 409
    return jsonify(message="Phone number created.", id=result)


@bp.put("/phones/<int:phone_id>")
@role_required("admin")
def update_phone(phone_id):
    """Change a phone number; it must stay unique."""
    number = json_field("phoneNumber").strip()
    if not number:
        return jsonify(error="Phone number is required."), 400
    return to_http(phones.update(phone_id, number), "Phone number updated.", "Phone number not found.",
                   "This phone number already exists.")
