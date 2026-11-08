import sqlite3

from db import get_db


def list_for_pop(pop_id):
    """Departments a POP is shared with, by name, with their access type."""
    rows = get_db().execute(
        'SELECT d.department_id, d.department_name, d.department_code, d.is_active, pd.access_type FROM "PopDepartment" pd '
        'JOIN "Department" d ON d.department_id = pd.department_id WHERE pd.pop_id = ? ORDER BY d.department_name',
        (pop_id,)).fetchall()
    return [{"id": r[0], "name": r[1] or "", "code": r[2] or "", "isActive": r[3] == 1, "accessType": r[4]} for r in rows]


def assign(pop_id, department_id, access_type):
    """Share a POP with a department: "ok", "not_found" or "conflict" (already shared)."""
    db = get_db()
    try:
        db.execute('INSERT INTO "PopDepartment" (pop_id, department_id, access_type) VALUES (?, ?, ?)',
                   (pop_id, department_id, access_type))
        db.commit()
        return "ok"
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
            return "not_found"
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise


def remove(pop_id, department_id):
    """Stop sharing a POP with a department; False if it wasn't shared."""
    db = get_db()
    cur = db.execute('DELETE FROM "PopDepartment" WHERE pop_id = ? AND department_id = ?', (pop_id, department_id))
    db.commit()
    return cur.rowcount > 0
