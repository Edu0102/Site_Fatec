from db import get_db
from repositories import utc_now


def _to_dict(r):
    """POP row → JSON-ready dict."""
    return {"id": r["pop_id"], "createdBy": r["created_by"], "updatedBy": r["updated_by"], "title": r["pop_title"],
            "description": r["pop_description"], "filePath": r["pop_file_path"], "version": r["pop_version"],
            "status": r["pop_status"], "createdAtUtc": r["created_at_utc"], "updatedAtUtc": r["updated_at_utc"]}


def _visible_rows(pop_id, user_id, role):
    """The one visibility rule: admins see every POP; others see published POPs shared with an active
    department they currently belong to. pop_id None = all of them, newest first."""
    now = utc_now()
    return get_db().execute(
        'SELECT p.* FROM "Pop" p WHERE (? IS NULL OR p.pop_id = ?) AND (? = \'admin\' OR (p.pop_status = \'published\' AND EXISTS ('
        ' SELECT 1 FROM "PopDepartment" pd JOIN "UserDepartment" ud ON ud.department_id = pd.department_id'
        ' JOIN "Department" d ON d.department_id = pd.department_id'
        ' WHERE pd.pop_id = p.pop_id AND ud.user_id = ? AND d.is_active = 1 AND ud.revoked_at_utc IS NULL'
        ' AND (ud.valid_from_utc IS NULL OR ud.valid_from_utc <= ?)'
        ' AND (ud.expires_at_utc IS NULL OR ud.expires_at_utc > ?)))) ORDER BY p.pop_id DESC',
        (pop_id, pop_id, role, user_id, now, now)).fetchall()


def get_visible(pop_id, user_id, role):
    """The POP row if this user may see it, else None."""
    rows = _visible_rows(pop_id, user_id, role)
    return rows[0] if rows else None


def get_visible_dict(pop_id, user_id, role):
    """The POP as a dict if this user may see it, else None."""
    row = get_visible(pop_id, user_id, role)
    return _to_dict(row) if row else None


def list_visible(user_id, role):
    """Every POP this user may see, newest first."""
    return [_to_dict(r) for r in _visible_rows(None, user_id, role)]


def add(actor_user_id, title, description, file_path, version, status):
    """Insert a POP authored by the actor; returns its id."""
    db = get_db()
    now = utc_now()
    cur = db.execute(
        'INSERT INTO "Pop" (created_by, updated_by, pop_title, pop_description, pop_file_path, pop_version, pop_status, '
        'created_at_utc, updated_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (actor_user_id, actor_user_id, title, description, file_path, version, status, now, now))
    db.commit()
    return cur.lastrowid


def update(actor_user_id, pop_id, title, description, file_path, version, status):
    """Replace a POP's fields; False if it doesn't exist."""
    db = get_db()
    cur = db.execute(
        'UPDATE "Pop" SET updated_by = ?, pop_title = ?, pop_description = ?, pop_file_path = ?, pop_version = ?, '
        'pop_status = ?, updated_at_utc = ? WHERE pop_id = ?',
        (actor_user_id, title, description, file_path, version, status, utc_now(), pop_id))
    db.commit()
    return cur.rowcount > 0


def archive(actor_user_id, pop_id):
    """Set a POP's status to archived; False if it doesn't exist."""
    db = get_db()
    cur = db.execute('UPDATE "Pop" SET pop_status = \'archived\', updated_by = ?, updated_at_utc = ? WHERE pop_id = ?',
                     (actor_user_id, utc_now(), pop_id))
    db.commit()
    return cur.rowcount > 0
