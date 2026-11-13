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


def test_link_phone_tag_tables_exist(tmp_path):
    path = str(tmp_path / "new.db")
    create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": path})
    assert {"Tag", "LinkTag", "PhoneTag"} <= _tables(path)


OLD_LINK_PHONE_POP = '''
CREATE TABLE "Pop" ("pop_id" INTEGER PRIMARY KEY AUTOINCREMENT, "created_by" INTEGER NOT NULL, "updated_by" INTEGER NOT NULL,
    "pop_title" TEXT NOT NULL, "pop_status" TEXT NOT NULL DEFAULT 'draft');
CREATE TABLE "Link" ("link_id" INTEGER PRIMARY KEY AUTOINCREMENT, "link_path" TEXT NOT NULL UNIQUE,
    "created_at_utc" TEXT, "updated_at_utc" TEXT);
CREATE TABLE "PhoneNumber" ("phone_id" INTEGER PRIMARY KEY AUTOINCREMENT, "phone_number" TEXT NOT NULL UNIQUE,
    "created_at_utc" TEXT, "updated_at_utc" TEXT);
CREATE TABLE "PopLink" ("pop_link_id" INTEGER PRIMARY KEY AUTOINCREMENT, "pop_id" INTEGER NOT NULL, "link_id" INTEGER NOT NULL,
    UNIQUE ("pop_id", "link_id"), FOREIGN KEY ("pop_id") REFERENCES "Pop"("pop_id"), FOREIGN KEY ("link_id") REFERENCES "Link"("link_id"));
CREATE TABLE "PopPhone" ("pop_phone_id" INTEGER PRIMARY KEY AUTOINCREMENT, "pop_id" INTEGER NOT NULL, "phone_id" INTEGER NOT NULL,
    UNIQUE ("pop_id", "phone_id"), FOREIGN KEY ("pop_id") REFERENCES "Pop"("pop_id"), FOREIGN KEY ("phone_id") REFERENCES "PhoneNumber"("phone_id"));
INSERT INTO "Pop" (pop_id, created_by, updated_by, pop_title) VALUES (1, 1, 1, 'P');
INSERT INTO "Link" (link_id, link_path) VALUES (7, 'https://a.com');
INSERT INTO "PhoneNumber" (phone_id, phone_number) VALUES (9, '1234');
INSERT INTO "PopLink" (pop_id, link_id) VALUES (1, 7);
INSERT INTO "PopPhone" (pop_id, phone_id) VALUES (1, 9);
'''


def test_old_link_and_phone_tables_migrated(tmp_path):
    path = str(tmp_path / "old.db")
    con = sqlite3.connect(path)
    con.execute(OLD_USER_TABLE)
    con.executescript(OLD_LINK_PHONE_POP)
    con.close()
    for _ in range(2):  # the second start must be a no-op
        create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": path})
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    assert con.execute('SELECT link_id, link_title, link_path, link_subject FROM "Link"').fetchall() == [
        (7, "https://a.com", "https://a.com", "")]
    assert con.execute('SELECT phone_id, contact_name, phone_number, department_id FROM "PhoneNumber"').fetchall() == [
        (9, "1234", "1234", None)]
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []
    assert con.execute('SELECT pp.phone_id FROM "PopPhone" pp JOIN "PhoneNumber" p USING (phone_id)').fetchall() == [(9,)]
    assert "PhoneNumber_old" not in _tables(path)
    con.execute('INSERT INTO "PhoneNumber" (contact_name, phone_number) VALUES (?, ?)', ("Outro", "1234"))  # no longer UNIQUE
    con.close()


def test_phone_migration_resumes_after_a_stop(tmp_path):
    path = str(tmp_path / "old.db")
    con = sqlite3.connect(path)
    con.execute(OLD_USER_TABLE)
    con.executescript(OLD_LINK_PHONE_POP)
    con.execute("PRAGMA legacy_alter_table = ON")
    con.execute('ALTER TABLE "PhoneNumber" RENAME TO "PhoneNumber_old"')  # the step before a crash
    con.close()
    create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": path})
    con = sqlite3.connect(path)
    assert con.execute('SELECT phone_id, contact_name FROM "PhoneNumber"').fetchall() == [(9, "1234")]
    assert "PhoneNumber_old" not in _tables(path)
    con.close()
