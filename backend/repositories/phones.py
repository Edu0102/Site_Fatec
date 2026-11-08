import sqlite3

from db import get_db
from repositories import utc_now


def _to_dict(r):
    """Phone row → JSON-ready dict."""
    return {"id": r["phone_id"], "phoneNumber": r["phone_number"], "createdAtUtc": r["created_at_utc"],
            "updatedAtUtc": r["updated_at_utc"]}


def get_all():
    """All phone numbers, by id."""
    rows = get_db().execute(
        'SELECT phone_id, phone_number, created_at_utc, updated_at_utc FROM "PhoneNumber" ORDER BY phone_id').fetchall()
    return [_to_dict(r) for r in rows]


def get_for_pop(pop_id):
    """The phone numbers assigned to a POP, by id."""
    rows = get_db().execute(
        'SELECT p.phone_id, p.phone_number, p.created_at_utc, p.updated_at_utc FROM "PhoneNumber" p '
        'JOIN "PopPhone" pp ON pp.phone_id = p.phone_id WHERE pp.pop_id = ? ORDER BY p.phone_id', (pop_id,)).fetchall()
    return [_to_dict(r) for r in rows]


def add(phone_number):
    """Insert a phone number; returns its new id, or "conflict" if the number already exists."""
    db = get_db()
    now = utc_now()
    try:
        cur = db.execute('INSERT INTO "PhoneNumber" (phone_number, created_at_utc, updated_at_utc) VALUES (?, ?, ?)',
                         (phone_number, now, now))
        db.commit()
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise
    return cur.lastrowid


def update(phone_id, phone_number):
    """Change a phone number: "ok", "not_found" or "conflict" (number used by another row)."""
    db = get_db()
    try:
        cur = db.execute('UPDATE "PhoneNumber" SET phone_number = ?, updated_at_utc = ? WHERE phone_id = ?',
                         (phone_number, utc_now(), phone_id))
        db.commit()
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise
    return "ok" if cur.rowcount else "not_found"
