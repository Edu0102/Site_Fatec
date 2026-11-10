import sqlite3

from db import get_db
from repositories import utc_now


def _to_dict(r):
    """Link row → JSON-ready dict."""
    return {"id": r["link_id"], "path": r["link_path"], "createdAtUtc": r["created_at_utc"],
            "updatedAtUtc": r["updated_at_utc"]}


def get_all():
    """Every link, by id."""
    return [_to_dict(r) for r in get_db().execute('SELECT * FROM "Link" ORDER BY link_id').fetchall()]


def add(path):
    """Insert a link and return its id; "conflict" if the path is already used."""
    db = get_db()
    now = utc_now()
    try:
        cur = db.execute('INSERT INTO "Link" (link_path, created_at_utc, updated_at_utc) VALUES (?, ?, ?)',
                         (path, now, now))
        db.commit()
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise
    return cur.lastrowid


def update(link_id, path):
    """Change a link's path: "ok", "not_found" or "conflict" (another link has the path)."""
    db = get_db()
    try:
        cur = db.execute('UPDATE "Link" SET link_path = ?, updated_at_utc = ? WHERE link_id = ?',
                         (path, utc_now(), link_id))
        db.commit()
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise
    return "ok" if cur.rowcount else "not_found"
