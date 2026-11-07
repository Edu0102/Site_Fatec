from flask import Blueprint, jsonify, session

from auth import current_user, login_required
from repositories import feedback, pops
from routes import POP_UNAVAILABLE, json_body, json_field, json_int, to_http

bp = Blueprint("feedback", __name__)


@bp.post("/feedback")
@login_required
def send_feedback():
    """Send feedback, optionally about a POP the user can see."""
    description = json_field("description").strip()
    if not description:
        return jsonify(error="Description is required."), 400
    pop_id = None
    if json_body().get("popId") is not None:
        pop_id = json_int("popId")
        if pop_id is None:
            return jsonify(error="POP id must be a whole number."), 400
        if pops.get_visible(pop_id, session["user_id"], current_user()["user_role"]) is None:
            return jsonify(POP_UNAVAILABLE), 404
    return jsonify(message="Feedback sent.", id=feedback.add(session["user_id"], pop_id, description))


@bp.get("/feedback")
@login_required
def list_feedback():
    """All feedback for admins, otherwise only the user's own, newest first."""
    only_mine = None if current_user()["user_role"] == "admin" else session["user_id"]
    return jsonify(feedback.get_list(only_mine))


@bp.post("/feedback/<int:feedback_id>/answer")
@login_required
def answer_feedback(feedback_id):
    """Answer a feedback item; the admin check is done against the database."""
    answer = json_field("answer").strip()
    if not answer:
        return jsonify(error="Answer is required."), 400
    result = feedback.answer(session["user_id"], feedback_id, answer)
    return to_http(result, "Feedback answered.", "Feedback not found.", "This feedback is closed.")


@bp.post("/feedback/<int:feedback_id>/close")
@login_required
def close_feedback(feedback_id):
    """Close a feedback item; the admin check is done against the database."""
    result = feedback.close(session["user_id"], feedback_id)
    return to_http(result, "Feedback closed.", "Feedback not found.", "This feedback is already closed.")
