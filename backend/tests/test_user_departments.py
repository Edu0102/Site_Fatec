from tests.conftest import login, login_admin, make_pop, register, run_sql

ASSIGNED = {"message": "User assigned to department."}


def setup(app, client):
    # Admin (user 1, logged in), basic user 2, one department; returns its id
    login_admin(app, client)
    register(client, email="b@test.com", name="Bia")
    client.post("/api/departments", json={"name": "Fiscal", "code": "fs"})
    return 1


def assign(client, user_id=2, dept_id=1, **extra):
    # POST /api/user-departments
    return client.post("/api/user-departments", json={"userId": user_id, "departmentId": dept_id, **extra})


def test_unauthenticated(client):
    assert assign(client).status_code == 401
    assert client.get("/api/me/departments").status_code == 401


def test_assign_and_list_mine(app, client):
    setup(app, client)
    r = assign(client)
    assert r.status_code == 200 and r.json == ASSIGNED
    login(client, "b@test.com")
    assert client.get("/api/me/departments").json == [{"id": 1, "name": "Fiscal", "code": "FS", "isActive": True}]
    with app.app_context():
        from db import get_db
        assert get_db().execute('SELECT access_type FROM "UserDepartment"').fetchone()[0] == "member"


def test_access_type_is_stored(app, client):
    setup(app, client)
    assign(client, accessType=" lead ")
    with app.app_context():
        from db import get_db
        assert get_db().execute('SELECT access_type FROM "UserDepartment"').fetchone()[0] == "lead"


def test_duplicate_only_while_active(app, client):
    setup(app, client)
    assign(client)
    r = assign(client)
    assert r.status_code == 409 and r.json == {"error": "This user is already assigned to the department."}
    run_sql(app, 'UPDATE "UserDepartment" SET revoked_at_utc = ?', ("2020-01-01T00:00:00.000000Z",))
    assert assign(client).status_code == 200


def test_errors(app, client):
    setup(app, client)
    for body in [{"userId": 999, "departmentId": 1}, {"userId": 2, "departmentId": 999}]:
        r = client.post("/api/user-departments", json=body)
        assert r.status_code == 404 and r.json == {"error": "User or department not found."}
    for body in [{}, {"userId": "2", "departmentId": 1}, {"userId": 2, "departmentId": True}]:
        r = client.post("/api/user-departments", json=body)
        assert r.status_code == 400 and r.json == {"error": "User id and department id must be whole numbers."}
    login(client, "b@test.com")
    r = assign(client)
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}


def test_my_departments_skips_revoked_and_expired(app, client):
    setup(app, client)
    client.post("/api/departments", json={"name": "Old", "code": "old"})
    client.post("/api/departments", json={"name": "Gone", "code": "gone"})
    assign(client, dept_id=1)
    assign(client, dept_id=2)
    assign(client, dept_id=3)
    run_sql(app, 'UPDATE "UserDepartment" SET expires_at_utc = ? WHERE department_id = 2', ("2020-01-01T00:00:00.000000Z",))
    run_sql(app, 'UPDATE "UserDepartment" SET revoked_at_utc = ? WHERE department_id = 3', ("2020-01-01T00:00:00.000000Z",))
    login(client, "b@test.com")
    assert [d["code"] for d in client.get("/api/me/departments").json] == ["FS"]


def test_assignment_opens_shared_pop(app, client):
    setup(app, client)
    pop = make_pop(app)
    run_sql(app, 'INSERT INTO "PopDepartment" (pop_id, department_id) VALUES (?, 1)', (pop,))
    login(client, "b@test.com")
    assert client.get(f"/api/pops/{pop}").status_code == 404
    login(client, "ana@test.com")
    assign(client)
    login(client, "b@test.com")
    assert client.get(f"/api/pops/{pop}").status_code == 200


# ---------- temporary access dates (São Paulo days) ----------

from datetime import datetime, timedelta, timezone  # noqa: E402
import sqlite3  # noqa: E402


def sp_day(offset=0):
    return (datetime.now(timezone(timedelta(hours=-3))).date() + timedelta(days=offset)).isoformat()


def rows(app):
    con = sqlite3.connect(app.config["DATABASE"])
    r = con.execute('SELECT access_type, valid_from_utc, expires_at_utc FROM "UserDepartment"').fetchall()
    con.close()
    return r


def test_assign_with_dates_stores_range(app, client):
    setup(app, client)
    r = assign(client, accessType="temporary", validFrom="2026-11-09", expiresAt="2026-11-15")
    assert r.json == ASSIGNED
    # São Paulo midnight is 03:00 UTC; the end date counts as a whole day
    assert rows(app) == [("temporary", "2026-11-09T03:00:00.000000Z", "2026-11-16T02:59:59.999999Z")]


def test_future_access_not_active_yet(app, client):
    setup(app, client)
    assign(client, validFrom=sp_day(1), expiresAt=sp_day(3))
    bia = app.test_client()
    login(bia, "b@test.com")
    assert bia.get("/api/me/departments").json == []
    client.delete("/api/departments/1/members/2")
    assign(client, validFrom=sp_day(0), expiresAt=sp_day(0))
    assert [d["name"] for d in bia.get("/api/me/departments").json] == ["Fiscal"]


def test_expired_access_gone(app, client):
    setup(app, client)
    run_sql(app, 'INSERT INTO "UserDepartment" (user_id, department_id, access_type, valid_from_utc, expires_at_utc) '
                 'VALUES (2, 1, ?, ?, ?)', ("temporary", "2000-01-01T00:00:00.000000Z", "2000-01-02T00:00:00.000000Z"))
    bia = app.test_client()
    login(bia, "b@test.com")
    assert bia.get("/api/me/departments").json == []


def test_date_validation(app, client):
    setup(app, client)
    bad = {"error": "Dates must be YYYY-MM-DD."}
    for extra, error in [({"validFrom": "2026-13-01"}, bad), ({"expiresAt": "15/11/2026"}, bad),
                         ({"validFrom": 123}, bad), ({"expiresAt": ""}, bad),
                         ({"validFrom": "2026-11-15", "expiresAt": "2026-11-14"},
                          {"error": "The end date can't be before the start date."})]:
        r = assign(client, **extra)
        assert r.status_code == 400 and r.json == error, extra
    assert rows(app) == []


def test_overlap_conflict(app, client):
    setup(app, client)
    assert assign(client).status_code == 200
    r = assign(client, accessType="temporary", validFrom=sp_day(0), expiresAt=sp_day(7))
    assert r.status_code == 409


# ---------- admin list with departments, and colleagues ----------

def three_people(app, client):
    # Admin Ana (1); Bia (2) and Ana in Fiscal (1); Caio (3) in Pessoal (2)
    setup(app, client)
    register(client, email="c@test.com", name="Caio")
    client.post("/api/departments", json={"name": "Pessoal", "code": "ps"})
    assign(client, user_id=1)
    assign(client, user_id=2)
    assign(client, user_id=3, dept_id=2)


def test_admin_user_list_includes_departments(app, client):
    setup(app, client)
    client.post("/api/departments", json={"name": "Pessoal", "code": "ps"})
    client.post("/api/departments", json={"name": "Contábil", "code": "ct"})
    assign(client)                                                   # fixed, Fiscal
    assign(client, dept_id=2, accessType="temporary", validFrom="2026-11-09", expiresAt="2099-11-15")
    assign(client, dept_id=3)
    client.delete("/api/departments/3/members/2")                    # revoked: not listed
    bia = [u for u in client.get("/api/admin/users").json if u["id"] == 2][0]
    assert [(d["name"], d["accessType"], d["validFromUtc"][:10], d["expiresAtUtc"]) for d in bia["departments"]] == [
        ("Fiscal", "member", bia["departments"][0]["validFromUtc"][:10], None),
        ("Pessoal", "temporary", "2026-11-09", "2099-11-16T02:59:59.999999Z")]
    assert set(bia["departments"][0]) == {"id", "name", "accessType", "validFromUtc", "expiresAtUtc"}


def test_colleagues(app, client):
    three_people(app, client)
    assert client.get("/api/me/colleagues").json == [
        {"id": 1, "name": "Fiscal", "members": [{"id": 1, "name": "Ana", "temporary": False},
                                                {"id": 2, "name": "Bia", "temporary": False}]}]


def test_colleagues_hide_inactive_users(app, client):
    three_people(app, client)
    client.put("/api/users/2", json={"isActive": False})
    assert [m["name"] for m in client.get("/api/me/colleagues").json[0]["members"]] == ["Ana"]


def test_colleagues_no_department(app, client):
    setup(app, client)
    assert client.get("/api/me/colleagues").json == []


def test_colleagues_unauthenticated(client):
    assert client.get("/api/me/colleagues").status_code == 401


def test_basic_user_cannot_see_admin_lists(app, client):
    three_people(app, client)
    caio = app.test_client()
    login(caio, "c@test.com")
    assert caio.get("/api/admin/users").status_code == 403
    assert caio.get("/api/departments/1/members").status_code == 403
    assert [d["name"] for d in caio.get("/api/me/colleagues").json] == ["Pessoal"]


def test_create_user_returns_id(app, client):
    setup(app, client)
    r = client.post("/api/users", json={"name": "Caio", "email": "caio@test.com", "password": "caiopass123"})
    assert r.json == {"message": "User registered.", "id": 3}


def test_odd_date_formats_rejected(app, client):
    setup(app, client)
    for extra in ({"validFrom": "2026-W45-3"}, {"expiresAt": "20261111xx"}, {"validFrom": "2026-1-1 "}):
        r = assign(client, **extra)
        assert r.status_code == 400 and r.json == {"error": "Dates must be YYYY-MM-DD."}, extra
    assert rows(app) == []


def test_far_future_end_date_is_not_a_crash(app, client):
    setup(app, client)
    r = assign(client, expiresAt="9999-12-31")
    assert r.status_code == 400 and r.json == {"error": "Dates must be YYYY-MM-DD."}


def test_already_ended_range_rejected(app, client):
    setup(app, client)
    r = assign(client, validFrom=sp_day(-10), expiresAt=sp_day(-1))
    assert r.status_code == 400 and r.json == {"error": "The end date can't be in the past."}
    assert rows(app) == []
    assert assign(client, validFrom=sp_day(-10), expiresAt=sp_day(0)).status_code == 200


def test_colleagues_lists_each_person_once(app, client):
    three_people(app, client)
    # Bia gets a temporary row on top of her fixed one (only possible outside the page)
    run_sql(app, 'INSERT INTO "UserDepartment" (user_id, department_id, access_type, valid_from_utc, expires_at_utc) '
                 'VALUES (2, 1, ?, ?, ?)', ("temporary", "2000-01-01T00:00:00.000000Z", "2999-01-01T00:00:00.000000Z"))
    members = client.get("/api/me/colleagues").json[0]["members"]
    assert members == [{"id": 1, "name": "Ana", "temporary": False}, {"id": 2, "name": "Bia", "temporary": False}]
