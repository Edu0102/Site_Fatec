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
