from flask import Blueprint, jsonify, session

from auth import current_user, login_required, role_required
from repositories import users
from routes import json_body, json_bool, json_field
from security import hash_password, verify_password

bp = Blueprint("users", __name__)


@bp.get("/users")
@login_required
def list_users():
    """Names of all active users."""
    return jsonify(users.active_names())


@bp.post("/users")
@role_required("admin")
def create_user():
    """Admins create a basic user after validating name, email and password."""
    name, email, password = json_field("name"), json_field("email"), json_field("password")
    if not name.strip() or not email.strip() or not password.strip():
        return jsonify(error="Name, email and password are required."), 400
    if len(password) < 8:
        return jsonify(error="Password must have at least 8 characters."), 400
    new_id = users.add(name.strip(), email.strip().lower(), hash_password(password))
    if new_id:
        return jsonify(message="User registered.", id=new_id)
    return jsonify(error="This email is already registered."), 409


@bp.put("/users/<int:user_id>")
@role_required("admin")
def update_user(user_id):
    """Admins change a user's name, email, role, active flag or password; never their own role or active flag."""
    body = json_body()
    if not {"name", "email", "role", "isActive", "password"} & set(body):
        return jsonify(error="Nothing to change."), 400
    name = json_field("name").strip() if "name" in body else None
    if name == "":
        return jsonify(error="Name can't be empty."), 400
    email = json_field("email").strip().lower() if "email" in body else None
    if email is not None and "@" not in email:
        return jsonify(error="Enter a valid email."), 400
    role = json_field("role").strip().lower() if "role" in body else None
    if role is not None and role not in ("admin", "basic"):
        return jsonify(error="Role must be admin or basic."), 400
    is_active = json_bool("isActive") if "isActive" in body else None
    if "isActive" in body and is_active is None:
        return jsonify(error="isActive must be true or false."), 400
    password = json_field("password") if "password" in body else None
    if password is not None and len(password) < 8:
        return jsonify(error="Password must have at least 8 characters."), 400
    if user_id == session["user_id"] and (role is not None or is_active is not None):
        return jsonify(error="You can't change your own role or active status."), 409
    if name is not None or email is not None:
        result = users.update_profile(user_id, name, email)
        if result == "not_found":
            return jsonify(error="User not found."), 404
        if result == "conflict":
            return jsonify(error="This email is already registered."), 409
    changed = users.update(user_id, role, None if is_active is None else int(is_active),
                           hash_password(password) if password else None, is_active is not None or password is not None)
    return (jsonify(message="User updated."), 200) if changed else (jsonify(error="User not found."), 404)


@bp.get("/admin/users")
@role_required("admin")
def admin_list_users():
    """Admins see every account with id, email, role and active flag."""
    return jsonify(users.list_all())


@bp.put("/me/password")
@login_required
def change_my_password():
    """Change your own password; other devices are logged out, this one stays in."""
    current, new = json_field("currentPassword"), json_field("newPassword")
    if not verify_password(current, current_user()["user_password_hash"]):
        return jsonify(error="Current password is wrong."), 400
    if len(new) < 8:
        return jsonify(error="Password must have at least 8 characters."), 400
    users.update(session["user_id"], None, None, hash_password(new), True)
    session["sv"] = users.get_by_id(session["user_id"])["user_session_version"]
    return jsonify(message="Password changed.")
