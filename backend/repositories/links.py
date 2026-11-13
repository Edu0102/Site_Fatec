import sqlite3

from db import get_db
from repositories import tags, utc_now


def to_dicts(rows):
    """Link rows → JSON-ready dicts, with their filters."""
    names = tags.names_for("link", [r["link_id"] for r in rows])
    return [{"id": r["link_id"], "title": r["link_title"], "description": r["link_description"], "url": r["link_path"],
             "subject": r["link_subject"], "tags": names.get(r["link_id"], []), "createdAtUtc": r["created_at_utc"],
             "updatedAtUtc": r["updated_at_utc"]} for r in rows]


def get_all():
    """Every link, by title."""
    return to_dicts(get_db().execute('SELECT * FROM "Link" ORDER BY link_title COLLATE NOCASE, link_id').fetchall())


def _save(sql, params, link_id_or_none, tag_names):
    """Run the insert/update plus the tags in one transaction; (cursor, None) or (None, "conflict")."""
    db = get_db()
    try:
        cur = db.execute(sql, params)
        item_id = link_id_or_none or cur.lastrowid
        if cur.rowcount:
            tags.set_for("link", item_id, tag_names)
        db.commit()
    except sqlite3.IntegrityError as e:
        db.rollback()
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return None, "conflict"
        raise
    return cur, None


def add(title, description, url, subject, tag_names):
    """Insert a link with its filters; its id, or "conflict" if another link has the URL."""
    now = utc_now()
    cur, error = _save('INSERT INTO "Link" (link_title, link_description, link_path, link_subject, created_at_utc, '
                       'updated_at_utc) VALUES (?, ?, ?, ?, ?, ?)', (title, description, url, subject, now, now),
                       None, tag_names)
    return error or cur.lastrowid


def update(link_id, title, description, url, subject, tag_names):
    """Change a link and its filters: "ok", "not_found" or "conflict" (another link has the URL)."""
    cur, error = _save('UPDATE "Link" SET link_title = ?, link_description = ?, link_path = ?, link_subject = ?, '
                       'updated_at_utc = ? WHERE link_id = ?', (title, description, url, subject, utc_now(), link_id),
                       link_id, tag_names)
    return error or ("ok" if cur.rowcount else "not_found")


def delete(link_id):
    """Delete a link, taking it off POPs and filters; False if it didn't exist."""
    db = get_db()
    db.execute('DELETE FROM "PopLink" WHERE link_id = ?', (link_id,))
    tags.clear_for("link", link_id)
    cur = db.execute('DELETE FROM "Link" WHERE link_id = ?', (link_id,))
    db.commit()
    return cur.rowcount > 0
