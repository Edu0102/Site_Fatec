import sqlite3

from app import create_app
from security import hash_password

OLD_USER_TABLE = '''CREATE TABLE "User" ("user_id" INTEGER NOT NULL UNIQUE, "user_name" TEXT, "user_email" TEXT UNIQUE,
    "user_password_hash" TEXT, "user_role" TEXT, "is_active" INTEGER, "created_at_utc" TEXT, "updated_at_utc" TEXT,
    PRIMARY KEY("user_id" AUTOINCREMENT))'''


def test_old_database_gets_session_version_column(tmp_path):
    path = str(tmp_path / "old.db")
    con = sqlite3.connect(path)
    con.execute(OLD_USER_TABLE)
    con.execute('INSERT INTO "User" (user_name, user_email, user_password_hash, user_role, is_active) VALUES (?, ?, ?, ?, 1)',
                ("Old", "old@test.com", hash_password("mypassword123"), "basic"))
    con.commit()
    con.close()
    app = create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": path})
    con = sqlite3.connect(path)
    assert con.execute('SELECT user_session_version FROM "User"').fetchone() == (0,)
    con.close()
    client = app.test_client()
    assert client.post("/api/auth/login", json={"email": "old@test.com", "password": "mypassword123"}).status_code == 200
    assert client.get("/api/auth/me").json["name"] == "Old"


def _tables(path):
    con = sqlite3.connect(path)
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    con.close()
    return names


def test_tool_tables_exist(tmp_path):
    path = str(tmp_path / "new.db")
    create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": path})
    assert {"Tool", "ToolUsage"} <= _tables(path)


def test_tool_tables_added_to_old_database(tmp_path):
    path = str(tmp_path / "old.db")
    con = sqlite3.connect(path)
    con.execute(OLD_USER_TABLE)
    con.execute('INSERT INTO "User" (user_name, user_email) VALUES (?, ?)', ("Old", "old@test.com"))
    con.commit()
    con.close()
    create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": path})
    assert {"Tool", "ToolUsage"} <= _tables(path)
    con = sqlite3.connect(path)
    assert con.execute('SELECT user_name FROM "User"').fetchall() == [("Old",)]
    con.close()
