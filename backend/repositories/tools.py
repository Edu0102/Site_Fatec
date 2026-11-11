from db import get_db
from repositories import utc_now


def _to_dict(r):
    """Tool row (joined with the user's usage) → JSON-ready dict."""
    return {"id": r["tool_id"], "name": r["tool_name"], "description": r["tool_description"], "url": r["tool_url"],
            "category": r["tool_category"], "icon": r["tool_icon"], "createdBy": r["created_by"],
            "opens": r["open_count"] or 0, "lastOpenedAtUtc": r["last_opened_at_utc"]}


def get_all(user_id):
    """Every tool, with how often this user opened it."""
    rows = get_db().execute('SELECT t.*, u.open_count, u.last_opened_at_utc FROM "Tool" t '
                            'LEFT JOIN "ToolUsage" u ON u.tool_id = t.tool_id AND u.user_id = ? ORDER BY t.tool_id',
                            (user_id,)).fetchall()
    return [_to_dict(r) for r in rows]


def add(user_id, name, description, url, category, icon):
    """Insert a tool created by user_id and return its id."""
    db = get_db()
    now = utc_now()
    cur = db.execute('INSERT INTO "Tool" (created_by, tool_name, tool_description, tool_url, tool_category, tool_icon, '
                     'created_at_utc, updated_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (user_id, name, description, url, category, icon, now, now))
    db.commit()
    return cur.lastrowid


def _check(tool_id, user_id, role):
    """"ok" if the user may change the tool (creator or admin), else "not_found" / "forbidden"."""
    row = get_db().execute('SELECT created_by FROM "Tool" WHERE tool_id = ?', (tool_id,)).fetchone()
    if row is None:
        return "not_found"
    return "ok" if role == "admin" or row["created_by"] == user_id else "forbidden"


def update(tool_id, user_id, role, name, description, url, category, icon):
    """Change a tool: "ok", "not_found" or "forbidden"."""
    result = _check(tool_id, user_id, role)
    if result == "ok":
        db = get_db()
        db.execute('UPDATE "Tool" SET tool_name = ?, tool_description = ?, tool_url = ?, tool_category = ?, '
                   'tool_icon = ?, updated_at_utc = ? WHERE tool_id = ?',
                   (name, description, url, category, icon, utc_now(), tool_id))
        db.commit()
    return result


def delete(tool_id, user_id, role):
    """Delete a tool and its usage rows: "ok", "not_found" or "forbidden"."""
    result = _check(tool_id, user_id, role)
    if result == "ok":
        db = get_db()
        db.execute('DELETE FROM "ToolUsage" WHERE tool_id = ?', (tool_id,))
        db.execute('DELETE FROM "Tool" WHERE tool_id = ?', (tool_id,))
        db.commit()
    return result


def record_open(tool_id, user_id):
    """Count one more open of the tool by this user: "ok" or "not_found"."""
    db = get_db()
    if db.execute('SELECT 1 FROM "Tool" WHERE tool_id = ?', (tool_id,)).fetchone() is None:
        return "not_found"
    now = utc_now()
    db.execute('INSERT INTO "ToolUsage" (user_id, tool_id, open_count, last_opened_at_utc) VALUES (?, ?, 1, ?) '
               'ON CONFLICT (user_id, tool_id) DO UPDATE SET open_count = open_count + 1, last_opened_at_utc = ?',
               (user_id, tool_id, now, now))
    db.commit()
    return "ok"
