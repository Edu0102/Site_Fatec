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
    assert client.post("/login", json={"email": "old@test.com", "password": "mypassword123"}).status_code == 200
    assert client.get("/me").json["name"] == "Old"
