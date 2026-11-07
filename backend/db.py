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
        db.executescript(schema)
        _add_missing_columns(db)


def _add_missing_columns(db):
    """Add columns that CREATE TABLE IF NOT EXISTS can't add to an older database file."""
    if "user_session_version" not in {r[1] for r in db.execute('PRAGMA table_info("User")')}:
        db.execute('ALTER TABLE "User" ADD COLUMN user_session_version INTEGER NOT NULL DEFAULT 0')
        db.commit()
