import sqlite3

from db import get_db
from repositories import users, utc_now


def get_all():
    """All departments as {id, name, code, isActive}."""
    rows = get_db().execute(
        'SELECT department_id, department_name, department_code, is_active FROM "Department"').fetchall()
    return [{"id": r["department_id"], "name": r["department_name"] or "",
             "code": r["department_code"] or "", "isActive": r["is_active"] == 1} for r in rows]


def add(actor_user_id, name, code):
    """Insert a department if the actor is an active admin: "ok", "conflict" or "forbidden"."""
    if not users.is_active_admin(actor_user_id):
        return "forbidden"
    db = get_db()
    now = utc_now()
    try:
        db.execute(
            'INSERT INTO "Department" (department_name, department_code, is_active, created_at_utc, updated_at_utc) '
            'VALUES (?, ?, 1, ?, ?)', (name, code, now, now))
        db.commit()
        return "ok"
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise


def update(department_id, name, code, is_active):
    """Rename / recode / (de)activate a department: "ok", "not_found" or "conflict" (code taken)."""
    db = get_db()
    try:
        cur = db.execute(
            'UPDATE "Department" SET department_name = ?, department_code = ?, is_active = ?, updated_at_utc = ? '
            'WHERE department_id = ?', (name, code, 1 if is_active else 0, utc_now(), department_id))
        db.commit()
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise
    return "ok" if cur.rowcount else "not_found"
