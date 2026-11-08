from tests.conftest import login, login_admin, make_pop, register

ASSIGNED = {"message": "Department assigned to POP."}


def setup(app, client):
    # Admin (user 1, logged in), basic Bia (user 2) in department 1 "FS"; POP 1 published but not shared yet
    login_admin(app, client)
    register(client, email="bia@test.com", name="Bia")
    client.post("/api/departments", json={"name": "Fiscal", "code": "fs"})
    client.post("/api/user-departments", json={"userId": 2, "departmentId": 1})
    return make_pop(app)


def share(client, pop_id=1, dept_id=1, **extra):
    # POST /api/pop-departments
    return client.post("/api/pop-departments", json={"popId": pop_id, "departmentId": dept_id, **extra})


def test_unauthenticated(client):
    assert client.get("/api/pops/1/departments").status_code == 401
    assert share(client).status_code == 401
    assert client.delete("/api/pops/1/departments/1").status_code == 401


def test_sharing_opens_and_unsharing_hides(app, client):
    pop = setup(app, client)
    bia = app.test_client()
    login(bia, "bia@test.com")
    assert bia.get(f"/api/pops/{pop}").status_code == 404
    r = share(client, pop)
    assert r.status_code == 200 and r.json == ASSIGNED
    assert bia.get(f"/api/pops/{pop}").status_code == 200
    r = client.delete(f"/api/pops/{pop}/departments/1")
    assert r.status_code == 200 and r.json == {"message": "Department removed from POP."}
    assert bia.get(f"/api/pops/{pop}").status_code == 404
    r = client.delete(f"/api/pops/{pop}/departments/1")
    assert r.status_code == 404 and r.json == {"error": "This department is not assigned to this POP."}


def test_list_pop_departments(app, client):
    pop = setup(app, client)
    client.post("/api/departments", json={"name": "Audit", "code": "au"})
    share(client, pop, 1)
    share(client, pop, 2, accessType=" edit ")
    expected = [{"id": 2, "name": "Audit", "code": "AU", "isActive": True, "accessType": "edit"},
                {"id": 1, "name": "Fiscal", "code": "FS", "isActive": True, "accessType": "read"}]
    assert client.get(f"/api/pops/{pop}/departments").json == expected
    bia = app.test_client()
    login(bia, "bia@test.com")
    assert bia.get(f"/api/pops/{pop}/departments").json == expected
    hidden = make_pop(app)
    r = bia.get(f"/api/pops/{hidden}/departments")
    assert r.status_code == 404 and r.json == {"error": "POP not found or not available."}


def test_errors(app, client):
    pop = setup(app, client)
    share(client, pop)
    r = share(client, pop)
    assert r.status_code == 409 and r.json == {"error": "This department is already assigned to the POP."}
    for body in [{"popId": 999, "departmentId": 1}, {"popId": pop, "departmentId": 999}]:
        r = client.post("/api/pop-departments", json=body)
        assert r.status_code == 404 and r.json == {"error": "POP or department not found."}
    for body in [{}, {"popId": "1", "departmentId": 1}, {"popId": 1, "departmentId": False}]:
        r = client.post("/api/pop-departments", json=body)
        assert r.status_code == 400 and r.json == {"error": "POP id and department id must be whole numbers."}
    login(client, "bia@test.com")
    assert share(client, pop).status_code == 403
    assert client.delete(f"/api/pops/{pop}/departments/1").status_code == 403
