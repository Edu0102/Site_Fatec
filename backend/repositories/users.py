import sqlite3

from db import get_db
from repositories import utc_now


def get_by_email(email):
    """Return the user row for an email, or None."""
    return get_db().execute(
        'SELECT user_id, user_name, user_email, user_password_hash, user_role, is_active '
        'FROM "User" WHERE user_email = ?', (email,)).fetchone()


def add(name, email, password_hash):
    """Insert a new active basic user; False when the email is already registered."""
    db = get_db()
    now = utc_now()
    try:
        db.execute(
            'INSERT INTO "User" (user_name, user_email, user_password_hash, user_role, is_active, '
            'created_at_utc, updated_at_utc) VALUES (?, ?, ?, \'basic\', 1, ?, ?)',
            (name, email, password_hash, now, now))
        db.commit()
        return True
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
