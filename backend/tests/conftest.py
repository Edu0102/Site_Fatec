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
