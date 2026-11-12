import sqlite3

from db import get_db
from repositories import utc_now


def assign(user_id, department_id, access_type, valid_from=None, expires_at=None):
    """Add a user to a department from valid_from (default now) until expires_at (default never):
    "ok", "not_found" (no such user/department) or "conflict" (already has a current or scheduled membership)."""
    db = get_db()
    now = utc_now()
    try:
        cur = db.execute(
            'INSERT INTO "UserDepartment" (user_id, department_id, access_type, valid_from_utc, expires_at_utc) '
            'SELECT ?, ?, ?, ?, ? '
            'WHERE NOT EXISTS (SELECT 1 FROM "UserDepartment" WHERE user_id = ? AND department_id = ? '
            'AND revoked_at_utc IS NULL AND (expires_at_utc IS NULL OR expires_at_utc > ?))',
            (user_id, department_id, access_type, valid_from or now, expires_at, user_id, department_id, now))
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


def colleagues(user_id):
    """The user's current active departments, each with its current active members (no emails)."""
    now = utc_now()
    result = []
    for dept in list_for_user(user_id):
        if not dept["isActive"]:
            continue
        rows = get_db().execute(
            'SELECT u.user_id, u.user_name, MIN(ud.expires_at_utc IS NOT NULL) FROM "UserDepartment" ud '
            'JOIN "User" u ON u.user_id = ud.user_id WHERE ud.department_id = ? AND u.is_active = 1 '
            'AND ud.revoked_at_utc IS NULL AND (ud.valid_from_utc IS NULL OR ud.valid_from_utc <= ?) '
            'AND (ud.expires_at_utc IS NULL OR ud.expires_at_utc > ?) GROUP BY u.user_id ORDER BY u.user_name, u.user_id',
            (dept["id"], now, now)).fetchall()
        result.append({"id": dept["id"], "name": dept["name"],
                       "members": [{"id": r[0], "name": r[1] or "", "temporary": r[2] == 1} for r in rows]})
    return result


def members(department_id):
    """Current members of a department, by name."""
    now = utc_now()
    rows = get_db().execute(
        'SELECT u.user_id, u.user_name, u.user_email, ud.access_type FROM "UserDepartment" ud '
        'JOIN "User" u ON u.user_id = ud.user_id WHERE ud.department_id = ? AND ud.revoked_at_utc IS NULL '
        'AND (ud.valid_from_utc IS NULL OR ud.valid_from_utc <= ?) AND (ud.expires_at_utc IS NULL OR ud.expires_at_utc > ?) '
        'ORDER BY u.user_name, u.user_id', (department_id, now, now)).fetchall()
    return [{"id": r[0], "name": r[1] or "", "email": r[2] or "", "accessType": r[3]} for r in rows]


def remove(user_id, department_id):
    """Revoke the user's active membership (kept as history); False if they weren't a member."""
    db = get_db()
    now = utc_now()
    cur = db.execute(
        'UPDATE "UserDepartment" SET revoked_at_utc = ? WHERE user_id = ? AND department_id = ? '
        'AND revoked_at_utc IS NULL AND (expires_at_utc IS NULL OR expires_at_utc > ?)',
        (now, user_id, department_id, now))
    db.commit()
    return cur.rowcount > 0
