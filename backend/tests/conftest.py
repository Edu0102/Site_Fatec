import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    # Fresh app with its own temporary database for each test
    return create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    # HTTP test client that keeps cookies between requests
    return app.test_client()


def register(client, email="ana@test.com", password="mypassword123", name="Ana"):
    # POST /register with the given fields
    return client.post("/register", json={"name": name, "email": email, "password": password})


def login(client, email="ana@test.com", password="mypassword123"):
    # POST /login with the given credentials
    return client.post("/login", json={"email": email, "password": password})


def login_basic(client, email="ana@test.com", name="Ana"):
    # Register a basic user and log in; returns the client
    register(client, email=email, name=name)
    login(client, email=email)
    return client


def login_admin(app, client, email="ana@test.com", name="Ana"):
    # Register a user, promote it to admin in the DB, then log in; returns the client
    register(client, email=email, name=name)
    set_user(app, email, user_role="admin")
    login(client, email=email)
    return client


def set_user(app, email, **cols):
    # Change columns of a user directly in the database (role, active flag, hash)
    import sqlite3
    allowed = {"user_role", "is_active", "user_password_hash"}
    con = sqlite3.connect(app.config["DATABASE"])
    for col, value in cols.items():
        assert col in allowed
        con.execute(f'UPDATE "User" SET {col} = ? WHERE user_email = ?', (value, email))
    con.commit()
    con.close()


def run_sql(app, sql, params=()):
    # Run one write statement on the test database; returns the new row id
    import sqlite3
    con = sqlite3.connect(app.config["DATABASE"])
    cur = con.execute(sql, params)
    con.commit()
    con.close()
    return cur.lastrowid


def make_pop(app, creator_id=1, status="published", title="POP 1"):
    # Insert a POP directly; returns its pop_id
    return run_sql(app, 'INSERT INTO "Pop" (created_by, updated_by, pop_title, pop_status) VALUES (?, ?, ?, ?)',
                   (creator_id, creator_id, title, status))


def give_access(app, user_id, pop_id, valid_from=None, expires=None, revoked=None):
    # Put the user in a new department that can see the POP
    dept = run_sql(app, 'INSERT INTO "Department" (department_name, department_code, is_active) VALUES (?, ?, 1)',
                   (f"D{pop_id}-{user_id}", f"D{pop_id}U{user_id}"))
    run_sql(app, 'INSERT INTO "PopDepartment" (pop_id, department_id) VALUES (?, ?)', (pop_id, dept))
    run_sql(app, 'INSERT INTO "UserDepartment" (user_id, department_id, access_type, valid_from_utc, expires_at_utc, revoked_at_utc) '
                 'VALUES (?, ?, ?, ?, ?, ?)', (user_id, dept, "member", valid_from, expires, revoked))
