from db import get_db
from repositories import users, utc_now


def _to_json(r):
    """One feedback row as the camelCase dict the frontend expects."""
    return {"id": r["feedback_id"], "userId": r["user_id"], "popId": r["pop_id"], "answeredBy": r["answered_by"],
            "description": r["feedback_description"], "status": r["feedback_status"], "answer": r["feedback_answer"],
            "createdAtUtc": r["created_at_utc"], "answeredAtUtc": r["answered_at_utc"]}


def add(user_id, pop_id, description):
    """Insert an open feedback item and return its new id."""
    db = get_db()
    cur = db.execute(
        'INSERT INTO "Feedback" (user_id, pop_id, feedback_description, feedback_status, created_at_utc) '
        "VALUES (?, ?, ?, 'open', ?)", (user_id, pop_id, description, utc_now()))
    db.commit()
    return cur.lastrowid


def get_list(user_id=None):
    """Feedback newest first; only this user's when user_id is given."""
    rows = get_db().execute(
        'SELECT * FROM "Feedback" WHERE (? IS NULL OR user_id = ?) ORDER BY feedback_id DESC',
        (user_id, user_id)).fetchall()
    return [_to_json(r) for r in rows]


def _outcome(cur, feedback_id):
    """Commit and turn an UPDATE guarded by "not closed" into "ok", "conflict" (closed) or "not_found"."""
    db = get_db()
    db.commit()
    if cur.rowcount:
        return "ok"
    exists = db.execute('SELECT 1 FROM "Feedback" WHERE feedback_id = ?', (feedback_id,)).fetchone()
    return "conflict" if exists else "not_found"


def answer(actor_user_id, feedback_id, answer):
    """Answer a feedback item if the actor is an active admin and it is not closed."""
    if not users.is_active_admin(actor_user_id):
        return "forbidden"
    cur = get_db().execute(
        "UPDATE \"Feedback\" SET feedback_answer = ?, answered_by = ?, answered_at_utc = ?, feedback_status = 'answered' "
        "WHERE feedback_id = ? AND feedback_status != 'closed'", (answer, actor_user_id, utc_now(), feedback_id))
    return _outcome(cur, feedback_id)


def close(actor_user_id, feedback_id):
    """Close a feedback item if the actor is an active admin and it is not already closed."""
    if not users.is_active_admin(actor_user_id):
        return "forbidden"
    cur = get_db().execute(
        "UPDATE \"Feedback\" SET feedback_status = 'closed' WHERE feedback_id = ? AND feedback_status != 'closed'",
        (feedback_id,))
    return _outcome(cur, feedback_id)
