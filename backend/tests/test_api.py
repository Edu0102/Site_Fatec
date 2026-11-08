import pytest

from app import create_app
from db import get_db


def test_schema_created(app):
    with app.app_context():
        names = {r[0] for r in get_db().execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"User", "Department", "UserDepartment", "Pop", "Link", "PhoneNumber",
            "PopLink", "PopPhone", "PopDepartment"} <= names


def test_missing_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setattr("app.load_dotenv", lambda: None)  # ignore a real backend/.env
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"DATABASE": ":memory:"})


from tests.conftest import login, login_admin, login_basic, register, set_user, sign_up

REQUIRED = {"error": "Name, email and password are required."}


def as_root(app, client):
    # Log in as an admin whose email doesn't clash with the users the sign-up tests create
    return login_admin(app, client, email="root@test.com", name="Root")


def test_sign_up_needs_admin(app, client):
    assert sign_up(client).status_code == 401
    login_basic(client, email="b@test.com")
    r = sign_up(client)
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}


def test_register_ok(app, client):
    as_root(app, client)
    r = sign_up(client)
    assert r.status_code == 200 and r.json == {"message": "User registered."}


def test_register_duplicate(app, client):
    as_root(app, client)
    sign_up(client)
    r = sign_up(client)
    assert r.status_code == 409 and r.json == {"error": "This email is already registered."}


def test_register_short_password(app, client):
    as_root(app, client)
    r = sign_up(client, password="1234567")
    assert r.status_code == 400 and r.json == {"error": "Password must have at least 8 characters."}
    assert sign_up(client, password="       x").status_code == 200


@pytest.mark.parametrize("body", [
    {"name": " ", "email": "a@b.c", "password": "mypassword123"},
    {},
    {"name": "Ana", "email": 123, "password": "mypassword123"},
    {"name": None, "email": "a@b.c", "password": "mypassword123"},
    [1, 2],
])
def test_register_missing_fields(app, client, body):
    as_root(app, client)
    r = client.post("/api/users", json=body)
    assert r.status_code == 400 and r.json == REQUIRED


def test_register_non_json_body(app, client):
    as_root(app, client)
    r = client.post("/api/users", data="hello", content_type="text/plain")
    assert r.status_code == 400 and r.json == REQUIRED


def test_email_normalized(app, client):
    as_root(app, client)
    sign_up(client, email="  Ana@Test.COM ")
    assert sign_up(client, email="ana@test.com").status_code == 409
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
        client.post("/api/auth/login", json={}),
        client.post("/api/auth/login", json={"email": 1, "password": 2}),
        client.post("/api/auth/login", data="x", content_type="text/plain"),
    ]
    assert {r.status_code for r in responses} == {401}
    assert len({r.get_data() for r in responses}) == 1


def test_me(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401 and r.json == {"error": "Not authenticated."}
    register(client)
    login(client)
    r = client.get("/api/auth/me")
    assert r.status_code == 200 and r.json == {"id": 1, "name": "Ana", "email": "ana@test.com", "role": "basic"}


def test_logout(client):
    r = client.post("/api/auth/logout")
    assert r.status_code == 200 and r.json == {"message": "Logged out."}
    register(client)
    login(client)
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_users_list(app, client):
    assert client.get("/api/users").status_code == 401
    register(client)
    register(client, email="bob@test.com", name="Bob")
    set_user(app, "bob@test.com", is_active=0)
    login(client)
    r = client.get("/api/users")
    assert r.status_code == 200 and r.json == ["Ana"]


def test_departments_list(app, client):
    assert client.get("/api/departments").status_code == 401
    login_admin(app, client)
    r = client.get("/api/departments")
    assert r.status_code == 200 and r.json == []
    client.post("/api/departments", json={"name": " IT ", "code": " ti "})
    assert client.get("/api/departments").json == [{"id": 1, "name": "IT", "code": "TI", "isActive": True}]


def test_department_create(app, client):
    login_admin(app, client)
    r = client.post("/api/departments", json={"name": "IT", "code": "TI"})
    assert r.status_code == 200 and r.json == {"message": "Department created."}
    for code in ["TI", "Ti"]:
        r = client.post("/api/departments", json={"name": "Other", "code": code})
        assert r.status_code == 409 and r.json == {"error": "This department code already exists."}
    for body in [{"name": "  ", "code": "X"}, {"name": "X", "code": " "}, {}]:
        r = client.post("/api/departments", json=body)
        assert r.status_code == 400 and r.json == {"error": "Name and code are required."}


def test_department_create_forbidden(client):
    assert client.post("/api/departments", json={"name": "No", "code": "NO"}).status_code == 401
    register(client)
    login(client)
    r = client.post("/api/departments", json={"name": "No", "code": "NO"})
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}


def test_stale_admin_cookie(app, client):
    login_admin(app, client)
    set_user(app, "ana@test.com", user_role="basic")
    assert client.post("/api/departments", json={"name": "IT", "code": "TI"}).status_code == 403
    assert client.delete("/api/users/1/photo").status_code == 403  # role is read from the database on every request


def test_lone_surrogate_is_rejected(app, client):
    as_root(app, client)
    raw = r'{"name":"a","email":"s@x.com","password":"abcdefgh\ud800"}'
    r = client.post("/api/users", data=raw, content_type="application/json")
    assert r.status_code == 400 and r.json == REQUIRED
    raw = r'{"email":"s\ud800@x.com","password":"abcdefgh"}'
    assert client.post("/api/auth/login", data=raw, content_type="application/json").status_code == 401


def test_cookie_samesite_lax(client):
    register(client)
    assert "SameSite=Lax" in login(client).headers["Set-Cookie"]


def test_cookie_holds_only_id_and_version(app, client):
    register(client)
    login(client)
    payload = app.session_interface.get_signing_serializer(app).loads(client.get_cookie("site_auth").value)
    assert {k for k in payload if not k.startswith("_")} == {"user_id", "sv"}  # "_permanent" is Flask's own flag
    assert "ana@test.com" not in str(payload)


def test_deactivated_user_loses_session(app, client):
    register(client)
    login(client)
    set_user(app, "ana@test.com", is_active=0)
    assert client.get("/api/auth/me").status_code == 401


def test_logout_kills_copied_cookie(app, client):
    register(client)
    login(client)
    copied = client.get_cookie("site_auth").value
    client.post("/api/auth/logout")
    thief = app.test_client()
    thief.set_cookie("site_auth", copied)
    r = thief.get("/api/auth/me")
    assert r.status_code == 401 and r.json == {"error": "Not authenticated."}
    login(client)  # logging in again still works
    assert client.get("/api/auth/me").status_code == 200
