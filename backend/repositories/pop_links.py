import sqlite3

from db import get_db
from repositories.links import _to_dict


def list_for_pop(pop_id):
    """Links assigned to a POP, by id."""
    rows = get_db().execute(
        'SELECT l.* FROM "Link" l JOIN "PopLink" pl ON pl.link_id = l.link_id WHERE pl.pop_id = ? ORDER BY l.link_id',
        (pop_id,)).fetchall()
    return [_to_dict(r) for r in rows]


def assign(pop_id, link_id):
    """Assign a link to a POP: "ok", "not_found" (no such POP or link) or "conflict" (already assigned)."""
    db = get_db()
    try:
        db.execute('INSERT INTO "PopLink" (pop_id, link_id) VALUES (?, ?)', (pop_id, link_id))
        db.commit()
        return "ok"
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
            return "not_found"
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise


def remove(pop_id, link_id):
    """Unassign a link from a POP; False if it wasn't assigned."""
    db = get_db()
    cur = db.execute('DELETE FROM "PopLink" WHERE pop_id = ? AND link_id = ?', (pop_id, link_id))
    db.commit()
    return cur.rowcount > 0
