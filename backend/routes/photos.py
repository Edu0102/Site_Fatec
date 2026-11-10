from flask import Blueprint, Response, jsonify, request, session

from auth import login_required, role_required
from repositories import photos

bp = Blueprint("photos", __name__)
MAX_PHOTO_BYTES = 2 * 1024 * 1024
TOO_BIG = {"error": "Photo must be at most 2 MB."}
NOT_FOUND = {"error": "Photo not found."}


def image_type(data):
    """The image MIME type from the file's first bytes; None if it is not JPEG, PNG or WebP."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


@bp.put("/me/photo")
@login_required
def save_my_photo():
    """Upload or replace the logged-in user's photo (multipart field "photo")."""
    file = request.files.get("photo")
    data = file.read(MAX_PHOTO_BYTES + 1) if file else b""
    if not data:
        return jsonify(error="Photo is required."), 400
    if len(data) > MAX_PHOTO_BYTES:
        return jsonify(TOO_BIG), 413
    content_type = image_type(data)
    if content_type is None:
        return jsonify(error="Photo must be a JPEG, PNG or WebP image."), 400
    photos.save(session["user_id"], data, content_type)
    return jsonify(message="Photo saved.")


@bp.get("/users/<int:user_id>/photo")
@login_required
def get_photo(user_id):
    """Any logged-in user may see a user's photo."""
    row = photos.get(user_id)
    if row is None:
        return jsonify(NOT_FOUND), 404
    return Response(row["photo_data"], mimetype=row["photo_content_type"], headers={"X-Content-Type-Options": "nosniff"})


@bp.delete("/me/photo")
@login_required
def delete_my_photo():
    """Remove the logged-in user's own photo."""
    return (jsonify(message="Photo deleted."), 200) if photos.delete(session["user_id"]) else (jsonify(NOT_FOUND), 404)


@bp.delete("/users/<int:user_id>/photo")
@role_required("admin")
def delete_user_photo(user_id):
    """Admins may remove anyone's photo (e.g. an inappropriate one)."""
    return (jsonify(message="Photo deleted."), 200) if photos.delete(user_id) else (jsonify(NOT_FOUND), 404)
