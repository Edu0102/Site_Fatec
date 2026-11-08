from db import get_db
from repositories import utc_now


def save(user_id, data, content_type):
    """Create or replace the user's photo."""
    db = get_db()
    db.execute(
        'INSERT INTO "UserPhoto" (user_id, photo_data, photo_content_type, updated_at_utc) VALUES (?, ?, ?, ?) '
        'ON CONFLICT(user_id) DO UPDATE SET photo_data = excluded.photo_data, '
        'photo_content_type = excluded.photo_content_type, updated_at_utc = excluded.updated_at_utc',
        (user_id, data, content_type, utc_now()))
    db.commit()


def get(user_id):
    """The user's photo row (photo_data, photo_content_type), or None."""
    return get_db().execute('SELECT photo_data, photo_content_type FROM "UserPhoto" WHERE user_id = ?', (user_id,)).fetchone()


def delete(user_id):
    """Remove the user's photo; False if there was none."""
    db = get_db()
    cur = db.execute('DELETE FROM "UserPhoto" WHERE user_id = ?', (user_id,))
    db.commit()
    return cur.rowcount > 0
