from db import get_db
from repositories import utc_now

def _to_dict(r):
    """Checklist row → JSON-ready dict."""
    return {"id": r["checklist_id"], "popId": r["pop_id"], "userId": r["user_id"], "description": r["checklist_description"],
            "createdAtUtc": r["created_at_utc"], "completedAtUtc": r["completed_at_utc"]}


def create(pop_id, user_id, description):
    """Start a checklist with one unchecked item per standard check of the POP, in one transaction; returns its id."""
    db = get_db()
    with db:
        new_id = db.execute(
            'INSERT INTO "Checklist" (pop_id, user_id, checklist_description, created_at_utc) VALUES (?, ?, ?, ?)',
            (pop_id, user_id, description, utc_now())).lastrowid
        db.execute(
            'INSERT INTO "ChecklistItemResult" (checklist_id, standard_check_id) '
            'SELECT ?, standard_check_id FROM "StandardCheck" WHERE pop_id = ?', (new_id, pop_id))
    return new_id


def get(checklist_id):
    """One checklist with its items ordered by check order, or None."""
    db = get_db()
    row = db.execute('SELECT checklist_id, pop_id, user_id, checklist_description, created_at_utc, completed_at_utc FROM "Checklist" WHERE checklist_id = ?', (checklist_id,)).fetchone()
    if row is None:
        return None
    items = db.execute(
        'SELECT r.standard_check_id, s.check_text, s.check_order, r.is_checked FROM "ChecklistItemResult" r '
        'JOIN "StandardCheck" s ON s.standard_check_id = r.standard_check_id WHERE r.checklist_id = ? '
        'ORDER BY s.check_order, s.standard_check_id', (checklist_id,)).fetchall()
    return {**_to_dict(row), "items": [{"standardCheckId": i[0], "checkText": i[1], "checkOrder": i[2],
                                        "isChecked": i[3] == 1} for i in items]}


def list_for_user(user_id):
    """The user's checklists, newest first, without items."""
    rows = get_db().execute('SELECT checklist_id, pop_id, user_id, checklist_description, created_at_utc, completed_at_utc FROM "Checklist" WHERE user_id = ? ORDER BY checklist_id DESC', (user_id,))
    return [_to_dict(r) for r in rows]


def _owned_state(checklist_id, user_id):
    """"not_found" if the user doesn't own it, "conflict" if completed, else None."""
    row = get_db().execute('SELECT completed_at_utc FROM "Checklist" WHERE checklist_id = ? AND user_id = ?',
                           (checklist_id, user_id)).fetchone()
    if row is None:
        return "not_found"
    return "conflict" if row[0] is not None else None


def set_item(user_id, checklist_id, standard_check_id, is_checked):
    """Tick or untick one item of the user's open checklist: "ok", "not_found" or "conflict"."""
    db = get_db()
    with db:
        cur = db.execute(
            'UPDATE "ChecklistItemResult" SET is_checked = ? WHERE checklist_id = ? AND standard_check_id = ? '
            'AND checklist_id IN (SELECT checklist_id FROM "Checklist" WHERE checklist_id = ? AND user_id = ? '
            'AND completed_at_utc IS NULL)', (1 if is_checked else 0, checklist_id, standard_check_id, checklist_id, user_id))
    return "ok" if cur.rowcount else _owned_state(checklist_id, user_id) or "not_found"


def complete(user_id, checklist_id):
    """Mark the user's checklist completed: "ok", "not_found" or "conflict"."""
    db = get_db()
    with db:
        cur = db.execute('UPDATE "Checklist" SET completed_at_utc = ? WHERE checklist_id = ? AND user_id = ? '
                         'AND completed_at_utc IS NULL', (utc_now(), checklist_id, user_id))
    return "ok" if cur.rowcount else _owned_state(checklist_id, user_id) or "conflict"


def delete(user_id, checklist_id):
    """Delete the user's own open checklist and its items: "ok", "not_found" or "conflict" (completed)."""
    db = get_db()
    with db:
        db.execute('DELETE FROM "ChecklistItemResult" WHERE checklist_id IN (SELECT checklist_id FROM "Checklist" '
                   'WHERE checklist_id = ? AND user_id = ? AND completed_at_utc IS NULL)', (checklist_id, user_id))
        cur = db.execute('DELETE FROM "Checklist" WHERE checklist_id = ? AND user_id = ? AND completed_at_utc IS NULL',
                         (checklist_id, user_id))
    return "ok" if cur.rowcount else _owned_state(checklist_id, user_id) or "conflict"
