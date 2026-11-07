import pytest

from app import create_app
from db import get_db


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200 and r.get_data(as_text=True) == "Server is running"


def test_schema_created(app):
    with app.app_context():
        names = {r[0] for r in get_db().execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"User", "Department", "UserDepartment", "Pop", "Link", "PhoneNumber",
            "PopLink", "PopPhone", "PopDepartment"} <= names


def test_missing_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"DATABASE": ":memory:"})


from tests.conftest import login, register, set_user

REQUIRED = {"error": "Name, email and password are required."}


def test_register_ok(client):
    r = register(client)
    assert r.status_code == 200 and r.json == {"message": "User registered."}


def test_register_duplicate(client):
    register(client)
    r = register(client)
    assert r.status_code == 409 and r.json == {"error": "This email is already registered."}


def test_register_short_password(client):
    r = register(client, password="1234567")
    assert r.status_code == 400 and r.json == {"error": "Password must have at least 8 characters."}
    assert register(client, password="       x").status_code == 200


@pytest.mark.parametrize("body", [
    {"name": " ", "email": "a@b.c", "password": "mypassword123"},
    {},
    {"name": "Ana", "email": 123, "password": "mypassword123"},
    {"name": None, "email": "a@b.c", "password": "mypassword123"},
    [1, 2],
])
def test_register_missing_fields(client, body):
    r = client.post("/register", json=body)
    assert r.status_code == 400 and r.json == REQUIRED


def test_register_non_json_body(client):
    r = client.post("/register", data="hello", content_type="text/plain")
    assert r.status_code == 400 and r.json == REQUIRED


def test_email_normalized(client):
    register(client, email="  Ana@Test.COM ")
    assert register(client, email="ana@test.com").status_code == 409
    assert login(client, email="ANA@test.com").status_code == 200


def test_login_ok(client):
    register(client)
    r = login(client)
    assert r.status_code == 200 and r.json == {"message": "Logged in."}
    cookie = r.headers["Set-Cookie"]
    assert "site_auth=" in cookie and "HttpOnly" in cookie and "Expires" in cookie


def test_login_failures_identical(app, client):
    register(client)
    register(client, email="off@test.com")
    set_user(app, "off@test.com", is_active=0)
    register(client, email="bad@test.com")
    set_user(app, "bad@test.com", user_password_hash="abc")
    responses = [
        login(client, password="wrongpassword"),
        login(client, email="nobody@test.com"),
        login(client, email="off@test.com"),
        login(client, email="bad@test.com"),
        client.post("/login", json={}),
        client.post("/login", json={"email": 1, "password": 2}),
        client.post("/login", data="x", content_type="text/plain"),
    ]
    assert {r.status_code for r in responses} == {401}
    assert len({r.get_data() for r in responses}) == 1


def test_me(client):
    r = client.get("/me")
    assert r.status_code == 401 and r.json == {"error": "Not authenticated."}
    register(client)
    login(client)
    r = client.get("/me")
    assert r.status_code == 200 and r.json == {"name": "Ana", "email": "ana@test.com", "role": "basic"}


def test_logout(client):
    r = client.post("/logout")
    assert r.status_code == 200 and r.json == {"message": "Logged out."}
    register(client)
    login(client)
    assert client.post("/logout").status_code == 200
    assert client.get("/me").status_code == 401
