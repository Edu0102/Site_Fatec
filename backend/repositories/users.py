import sqlite3

from db import get_db
from repositories import utc_now


def get_by_email(email):
    """Return the user row for an email, or None."""
    return get_db().execute(
        'SELECT user_id, user_name, user_email, user_password_hash, user_role, is_active, user_session_version FROM "User" WHERE user_email = ?', (email,)).fetchone()


def get_by_id(user_id):
    """Return the user row for an id, or None."""
    return get_db().execute(
        'SELECT user_id, user_name, user_email, user_password_hash, user_role, is_active, user_session_version FROM "User" WHERE user_id = ?', (user_id,)).fetchone()


def bump_session_version(user_id):
    """Invalidate every cookie issued to this user so far."""
    db = get_db()
    db.execute('UPDATE "User" SET user_session_version = user_session_version + 1 WHERE user_id = ?', (user_id,))
    db.commit()


def add(name, email, password_hash):
    """Insert a new active basic user and return its id; False when the email is already registered."""
    db = get_db()
    now = utc_now()
    try:
        cur = db.execute(
            'INSERT INTO "User" (user_name, user_email, user_password_hash, user_role, is_active, '
            'created_at_utc, updated_at_utc) VALUES (?, ?, ?, \'basic\', 1, ?, ?)',
            (name, email, password_hash, now, now))
        db.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return False


def active_names():
    """Names of all active users (NULL names skipped)."""
    rows = get_db().execute('SELECT user_name FROM "User" WHERE is_active = 1').fetchall()
    return [r["user_name"] for r in rows if r["user_name"] is not None]


def is_active_admin(user_id):
    """True if the user is an active admin in the database (not trusting the cookie)."""
    row = get_db().execute(
        'SELECT COUNT(*) FROM "User" WHERE user_id = ? AND user_role = \'admin\' AND is_active = 1',
        (user_id,)).fetchone()
    return row[0] > 0


def update(user_id, role, is_active, password_hash, end_sessions):
    """Change only the given fields (None = keep); end_sessions logs the user out everywhere. False if no such user."""
    db = get_db()
    cur = db.execute(
        'UPDATE "User" SET user_role = COALESCE(?, user_role), is_active = COALESCE(?, is_active), '
        'user_password_hash = COALESCE(?, user_password_hash), user_session_version = user_session_version + ?, '
        'updated_at_utc = ? WHERE user_id = ?',
        (role, is_active, password_hash, 1 if end_sessions else 0, utc_now(), user_id))
    db.commit()
    return cur.rowcount > 0


def update_profile(user_id, name, email):
    """Change name and/or email (None = keep): "ok", "not_found" or "conflict" (email used by someone else)."""
    db = get_db()
    try:
        cur = db.execute('UPDATE "User" SET user_name = COALESCE(?, user_name), user_email = COALESCE(?, user_email), '
                         'updated_at_utc = ? WHERE user_id = ?', (name, email, utc_now(), user_id))
        db.commit()
    except sqlite3.IntegrityError:
        return "conflict"
    return "ok" if cur.rowcount else "not_found"


def list_all():
    """Every account for the admin screen, by name (never the password hash), each with its memberships
    that are not revoked or expired (scheduled ones included)."""
    db = get_db()
    rows = db.execute(
        'SELECT user_id, user_name, user_email, user_role, is_active FROM "User" ORDER BY user_name, user_id').fetchall()
    memberships = {}
    for m in db.execute(
            'SELECT ud.user_id, d.department_id, d.department_name, ud.access_type, ud.valid_from_utc, ud.expires_at_utc '
            'FROM "UserDepartment" ud JOIN "Department" d ON d.department_id = ud.department_id '
            'WHERE ud.revoked_at_utc IS NULL AND (ud.expires_at_utc IS NULL OR ud.expires_at_utc > ?) '
            'ORDER BY d.department_name, ud.valid_from_utc', (utc_now(),)):
        memberships.setdefault(m[0], []).append({"id": m[1], "name": m[2] or "", "accessType": m[3],
                                                 "validFromUtc": m[4], "expiresAtUtc": m[5]})
    return [{"id": r[0], "name": r[1] or "", "email": r[2] or "", "role": r[3] or "user", "isActive": r[4] == 1,
             "departments": memberships.get(r[0], [])} for r in rows]
