import sqlite3

from db import get_db
from repositories import utc_now


def assign(user_id, department_id, access_type):
    """Add a user to a department: "ok", "not_found" (no such user/department) or "conflict" (already active)."""
    db = get_db()
    now = utc_now()
    try:
        cur = db.execute(
            'INSERT INTO "UserDepartment" (user_id, department_id, access_type, valid_from_utc) SELECT ?, ?, ?, ? '
            'WHERE NOT EXISTS (SELECT 1 FROM "UserDepartment" WHERE user_id = ? AND department_id = ? '
            'AND revoked_at_utc IS NULL AND (expires_at_utc IS NULL OR expires_at_utc > ?))',
            (user_id, department_id, access_type, now, user_id, department_id, now))
        db.commit()
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
            return "not_found"
        raise
    return "ok" if cur.rowcount else "conflict"


def list_for_user(user_id):
    """The user's current departments (not revoked, started, not expired), by name."""
    now = utc_now()
    rows = get_db().execute(
        'SELECT DISTINCT d.department_id, d.department_name, d.department_code, d.is_active FROM "UserDepartment" ud '
        'JOIN "Department" d ON d.department_id = ud.department_id WHERE ud.user_id = ? AND ud.revoked_at_utc IS NULL '
        'AND (ud.valid_from_utc IS NULL OR ud.valid_from_utc <= ?) AND (ud.expires_at_utc IS NULL OR ud.expires_at_utc > ?) '
        'ORDER BY d.department_name', (user_id, now, now)).fetchall()
    return [{"id": r[0], "name": r[1] or "", "code": r[2] or "", "isActive": r[3] == 1} for r in rows]
