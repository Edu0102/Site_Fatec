"""Filters (tags) of the Central de Links ("link") and Lista telefônica ("phone"); each page has its own list."""
import sqlite3

from db import get_db

# scope -> (join table, item id column); table names never come from user input
JOINS = {"link": ("LinkTag", "link_id"), "phone": ("PhoneTag", "phone_id")}


def get_all(scope):
    """The scope's filters as {id, name}, by name."""
    rows = get_db().execute('SELECT tag_id, tag_name FROM "Tag" WHERE tag_scope = ? ORDER BY tag_name',
                            (scope,)).fetchall()
    return [{"id": r["tag_id"], "name": r["tag_name"]} for r in rows]


def add(scope, name):
    """Create a filter; its id, or "conflict" if the scope has it already (case-insensitive)."""
    db = get_db()
    try:
        cur = db.execute('INSERT INTO "Tag" (tag_scope, tag_name) VALUES (?, ?)', (scope, name))
        db.commit()
    except sqlite3.IntegrityError as e:
        if e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return "conflict"
        raise
    return cur.lastrowid


def delete(tag_id):
    """Delete a filter and take it off every item; False if it didn't exist."""
    db = get_db()
    for table, _ in JOINS.values():
        db.execute(f'DELETE FROM "{table}" WHERE tag_id = ?', (tag_id,))
    cur = db.execute('DELETE FROM "Tag" WHERE tag_id = ?', (tag_id,))
    db.commit()
    return cur.rowcount > 0


def names_for(scope, item_ids):
    """{item id: [tag names, sorted]} for the given items; items without tags are absent."""
    table, col = JOINS[scope]
    ids = list(item_ids)
    rows = get_db().execute(
        f'SELECT j.{col} AS item_id, t.tag_name FROM "{table}" j JOIN "Tag" t ON t.tag_id = j.tag_id '
        f'WHERE j.{col} IN (SELECT value FROM json_each(?)) ORDER BY t.tag_name', (str(ids),)).fetchall()
    result = {}
    for r in rows:
        result.setdefault(r["item_id"], []).append(r["tag_name"])
    return result


def set_for(scope, item_id, names):
    """Replace an item's tags, creating missing filters (same name in other casing reuses it). Caller commits."""
    # shortcut: NOCASE folds ASCII only ("Débitos" vs "DÉBITOS" are two tags); fold in Python if that shows up.
    db = get_db()
    clear_for(scope, item_id)
    table, col = JOINS[scope]
    for name in names:
        db.execute('INSERT OR IGNORE INTO "Tag" (tag_scope, tag_name) VALUES (?, ?)', (scope, name))
        db.execute(f'INSERT OR IGNORE INTO "{table}" ({col}, tag_id) '
                   'SELECT ?, tag_id FROM "Tag" WHERE tag_scope = ? AND tag_name = ?', (item_id, scope, name))


def clear_for(scope, item_id):
    """Take every tag off an item. Caller commits."""
    table, col = JOINS[scope]
    get_db().execute(f'DELETE FROM "{table}" WHERE {col} = ?', (item_id,))
