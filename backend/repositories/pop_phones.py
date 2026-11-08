import sqlite3

from db import get_db


def add(pop_id, phone_id):
    """Assign a phone number to a POP: "ok", "not_found" (POP or phone missing) or "conflict" (already assigned)."""
    db = get_db()
    try:
        db.execute('INSERT INTO "PopPhone" (pop_id, phone_id) VALUES (?, ?)', (pop_id, phone_id))
        db.commit()
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
            return "not_found"
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise
    return "ok"


def remove(pop_id, phone_id):
    """Unassign a phone number from a POP; False if it was not assigned."""
    db = get_db()
    cur = db.execute('DELETE FROM "PopPhone" WHERE pop_id = ? AND phone_id = ?', (pop_id, phone_id))
    db.commit()
    return cur.rowcount > 0
