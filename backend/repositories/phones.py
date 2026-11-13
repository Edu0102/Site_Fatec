"""Lista telefônica contacts (table "PhoneNumber", kept for PopPhone)."""
import sqlite3

from db import get_db
from repositories import tags, utc_now

SELECT = ('SELECT p.*, d.department_name FROM "PhoneNumber" p '
          'LEFT JOIN "Department" d ON d.department_id = p.department_id ')
ORDER = ' ORDER BY p.contact_name COLLATE NOCASE, p.phone_id'


def _to_dicts(rows):
    """Contact rows → JSON-ready dicts, with their filters."""
    names = tags.names_for("phone", [r["phone_id"] for r in rows])
    return [{"id": r["phone_id"], "name": r["contact_name"], "departmentId": r["department_id"],
             "department": r["department_name"], "extension": r["phone_extension"], "phoneNumber": r["phone_number"],
             "email": r["contact_email"], "tags": names.get(r["phone_id"], []), "createdAtUtc": r["created_at_utc"],
             "updatedAtUtc": r["updated_at_utc"]} for r in rows]


def get_all():
    """Every contact, by name."""
    return _to_dicts(get_db().execute(SELECT + ORDER).fetchall())


def get_for_pop(pop_id):
    """The contacts assigned to a POP, by name."""
    rows = get_db().execute(SELECT + 'JOIN "PopPhone" pp ON pp.phone_id = p.phone_id WHERE pp.pop_id = ?' + ORDER,
                            (pop_id,)).fetchall()
    return _to_dicts(rows)


def _save(sql, params, phone_id, tag_names):
    """Run the write plus the tags in one transaction; (cursor, None) or (None, "bad_department")."""
    db = get_db()
    try:
        cur = db.execute(sql, params)
        if cur.rowcount:
            tags.set_for("phone", phone_id or cur.lastrowid, tag_names)
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
            return None, "bad_department"
        raise
    return cur, None


def add(name, department_id, extension, phone_number, email, tag_names):
    """Insert a contact; its id, or "bad_department" if the department doesn't exist."""
    now = utc_now()
    cur, error = _save('INSERT INTO "PhoneNumber" (contact_name, department_id, phone_extension, phone_number, '
                       'contact_email, created_at_utc, updated_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (name, department_id, extension, phone_number, email, now, now), None, tag_names)
    return error or cur.lastrowid


def update(phone_id, name, department_id, extension, phone_number, email, tag_names):
    """Change a contact: "ok", "not_found" or "bad_department"."""
    cur, error = _save('UPDATE "PhoneNumber" SET contact_name = ?, department_id = ?, phone_extension = ?, '
                       'phone_number = ?, contact_email = ?, updated_at_utc = ? WHERE phone_id = ?',
                       (name, department_id, extension, phone_number, email, utc_now(), phone_id), phone_id, tag_names)
    return error or ("ok" if cur.rowcount else "not_found")


def delete(phone_id):
    """Delete a contact, taking it off POPs and filters; False if it didn't exist."""
    db = get_db()
    db.execute('DELETE FROM "PopPhone" WHERE phone_id = ?', (phone_id,))
    tags.clear_for("phone", phone_id)
    cur = db.execute('DELETE FROM "PhoneNumber" WHERE phone_id = ?', (phone_id,))
    db.commit()
    return cur.rowcount > 0
