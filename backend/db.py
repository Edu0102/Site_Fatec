import os
import sqlite3

from flask import current_app, g


def get_db():
    """Return this request's SQLite connection, opening it on first use."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the request's connection, if one was opened."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create the tables from schema.sql (CREATE TABLE IF NOT EXISTS)."""
    with open(os.path.join(app.root_path, "schema.sql"), encoding="utf-8") as f:
        schema = f.read()
    with app.app_context():
        db = get_db()
        old_phone_table = _set_aside_old_phone_table(db)
        db.executescript(schema)
        if old_phone_table or _columns(db, "PhoneNumber_old"):  # second case: a start that stopped mid-migration
            _copy_old_phones(db)
        _add_missing_columns(db)


def _columns(db, table):
    """Column names of a table; empty set if the table doesn't exist."""
    return {r[1] for r in db.execute(f'PRAGMA table_info("{table}")')}


def _set_aside_old_phone_table(db):
    """Rename a pre-contacts PhoneNumber (phone_number UNIQUE, no name) so schema.sql can create the new one."""
    cols = _columns(db, "PhoneNumber")
    if not cols or "contact_name" in cols:
        return False
    db.commit()
    db.execute("PRAGMA foreign_keys = OFF")  # PopPhone keeps pointing at "PhoneNumber", refilled below
    db.execute("PRAGMA legacy_alter_table = ON")  # don't rewrite PopPhone's reference to the old name
    db.execute('ALTER TABLE "PhoneNumber" RENAME TO "PhoneNumber_old"')
    db.execute("PRAGMA legacy_alter_table = OFF")
    return True


def _copy_old_phones(db):
    """Move old phone rows into the new table, same ids; the number doubles as the name (there was none)."""
    db.execute('INSERT INTO "PhoneNumber" (phone_id, contact_name, phone_number, created_at_utc, updated_at_utc) '
               'SELECT phone_id, phone_number, phone_number, created_at_utc, updated_at_utc FROM "PhoneNumber_old"')
    db.execute('DROP TABLE "PhoneNumber_old"')
    db.commit()
    db.execute("PRAGMA foreign_keys = ON")


def _add_missing_columns(db):
    """Add columns that CREATE TABLE IF NOT EXISTS can't add to an older database file."""
    if "user_session_version" not in _columns(db, "User"):
        db.execute('ALTER TABLE "User" ADD COLUMN user_session_version INTEGER NOT NULL DEFAULT 0')
        db.commit()
    if "link_title" not in _columns(db, "Link"):
        for col in ("link_title", "link_description", "link_subject"):
            db.execute(f'ALTER TABLE "Link" ADD COLUMN {col} TEXT NOT NULL DEFAULT \'\'')
        db.execute('UPDATE "Link" SET link_title = link_path')  # old links had no title
        db.commit()
