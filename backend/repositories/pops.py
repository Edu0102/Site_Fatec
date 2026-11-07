from db import get_db
from repositories import utc_now


def get_visible(pop_id, user_id, role):
    """The POP row if this user may see it (admin: any; others: published + active department access), else None."""
    if role == "admin":
        return get_db().execute('SELECT * FROM "Pop" WHERE pop_id = ?', (pop_id,)).fetchone()
    now = utc_now()
    return get_db().execute(
        'SELECT p.* FROM "Pop" p WHERE p.pop_id = ? AND p.pop_status = \'published\' AND EXISTS ('
        ' SELECT 1 FROM "PopDepartment" pd JOIN "UserDepartment" ud ON ud.department_id = pd.department_id'
        ' WHERE pd.pop_id = p.pop_id AND ud.user_id = ? AND ud.revoked_at_utc IS NULL'
        ' AND (ud.valid_from_utc IS NULL OR ud.valid_from_utc <= ?)'
        ' AND (ud.expires_at_utc IS NULL OR ud.expires_at_utc > ?))',
        (pop_id, user_id, now, now)).fetchone()
