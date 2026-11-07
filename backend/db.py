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
        get_db().executescript(schema)
