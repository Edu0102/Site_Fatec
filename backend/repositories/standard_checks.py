import sqlite3

from db import get_db
from repositories import users


def list_for_pop(pop_id):
    """A POP's standard checks ordered by check_order, as {id, popId, checkText, checkOrder}."""
    rows = get_db().execute(
        'SELECT standard_check_id, pop_id, check_text, check_order FROM "StandardCheck" '
        'WHERE pop_id = ? ORDER BY check_order, standard_check_id', (pop_id,)).fetchall()
    return [{"id": r["standard_check_id"], "popId": r["pop_id"], "checkText": r["check_text"],
             "checkOrder": r["check_order"]} for r in rows]


def add(actor_user_id, pop_id, check_text, check_order):
    """Insert a check if the actor is an active admin: ("ok", new_id), ("forbidden", None) or ("not_found", None)."""
    if not users.is_active_admin(actor_user_id):
        return "forbidden", None
    db = get_db()
    try:
        cur = db.execute(
            'INSERT INTO "StandardCheck" (pop_id, check_text, check_order) VALUES (?, ?, ?)',
            (pop_id, check_text, check_order))
        db.commit()
        return "ok", cur.lastrowid
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
            return "not_found", None
        raise


def update(check_id, check_text, check_order):
    """Change a check's text and order; False if it doesn't exist."""
    db = get_db()
    cur = db.execute('UPDATE "StandardCheck" SET check_text = ?, check_order = ? WHERE standard_check_id = ?',
                     (check_text, check_order, check_id))
    db.commit()
    return cur.rowcount > 0


def delete(check_id):
    """Delete a check and its ticks in every checklist, in one transaction; False if it doesn't exist."""
    db = get_db()
    with db:
        db.execute('DELETE FROM "ChecklistItemResult" WHERE standard_check_id = ?', (check_id,))
        cur = db.execute('DELETE FROM "StandardCheck" WHERE standard_check_id = ?', (check_id,))
    return cur.rowcount > 0
