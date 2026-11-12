from tests.conftest import give_access, login, login_admin, login_basic, make_pop, register, run_sql


# ---------- GET /api/admin/users ----------

def test_admin_user_list(app, client):
    assert client.get("/api/admin/users").status_code == 401
    login_admin(app, client)
    register(client, email="bia@test.com", name="Bia")
    run_sql(app, 'UPDATE "User" SET is_active = 0 WHERE user_email = ?', ("bia@test.com",))
    r = client.get("/api/admin/users")
    assert r.status_code == 200
    assert r.json == [{"id": 1, "name": "Ana", "email": "ana@test.com", "role": "admin", "isActive": True, "departments": []},
                      {"id": 2, "name": "Bia", "email": "bia@test.com", "role": "basic", "isActive": False,
                       "departments": []}]
    login_basic(client, email="c@test.com")
    assert client.get("/api/admin/users").status_code == 403


# ---------- department members ----------

def dept_with_member(app, client):
    # Admin logged in; department 1 "FS" with Bia (user 2) as a member
    login_admin(app, client)
    register(client, email="bia@test.com", name="Bia")
    client.post("/api/departments", json={"name": "Fiscal", "code": "fs"})
    client.post("/api/user-departments", json={"userId": 2, "departmentId": 1, "accessType": "lead"})


def test_member_list(app, client):
    dept_with_member(app, client)
    r = client.get("/api/departments/1/members")
    assert r.status_code == 200
    assert r.json == [{"id": 2, "name": "Bia", "email": "bia@test.com", "accessType": "lead"}]
    assert client.get("/api/departments/999/members").json == []
    login(client, "bia@test.com")
    assert client.get("/api/departments/1/members").status_code == 403


def test_remove_member_ends_pop_access(app, client):
    dept_with_member(app, client)
    pop = make_pop(app)
    run_sql(app, 'INSERT INTO "PopDepartment" (pop_id, department_id) VALUES (?, 1)', (pop,))
    bia = app.test_client()
    login(bia, "bia@test.com")
    assert bia.get(f"/api/pops/{pop}").status_code == 200
    r = client.delete("/api/departments/1/members/2")
    assert r.status_code == 200 and r.json == {"message": "User removed from department."}
    assert bia.get(f"/api/pops/{pop}").status_code == 404
    assert client.get("/api/departments/1/members").json == []
    r = client.delete("/api/departments/1/members/2")
    assert r.status_code == 404 and r.json == {"error": "This user is not in the department."}
    assert client.post("/api/user-departments", json={"userId": 2, "departmentId": 1}).status_code == 200  # can rejoin
    login(bia, "bia@test.com")
    assert bia.delete("/api/departments/1/members/2").status_code == 403


# ---------- PUT /api/me/password ----------

def test_change_own_password(app, client):
    login_basic(client)
    other_device = app.test_client()
    login(other_device)
    r = client.put("/api/me/password", json={"currentPassword": "mypassword123", "newPassword": "a-new-password"})
    assert r.status_code == 200 and r.json == {"message": "Password changed."}
    assert client.get("/api/auth/me").status_code == 200        # this session stays logged in
    assert other_device.get("/api/auth/me").status_code == 401  # other devices are logged out
    assert login(other_device).status_code == 401
    assert login(other_device, password="a-new-password").status_code == 200


def test_change_own_password_errors(app, client):
    assert client.put("/api/me/password", json={}).status_code == 401
    login_basic(client)
    r = client.put("/api/me/password", json={"currentPassword": "wrong-one", "newPassword": "a-new-password"})
    assert r.status_code == 400 and r.json == {"error": "Current password is wrong."}
    r = client.put("/api/me/password", json={"currentPassword": "mypassword123", "newPassword": "short"})
    assert r.status_code == 400 and r.json == {"error": "Password must have at least 8 characters."}
    assert login(app.test_client()).status_code == 200  # nothing changed


# ---------- GET /api/checklists (admin) ----------

def test_admin_checklist_list(app, client):
    assert client.get("/api/checklists").status_code == 401
    register(client)
    pop = make_pop(app)
    give_access(app, 1, pop)
    login(client)
    client.post(f"/api/pops/{pop}/checklists", json={"description": "first"})
    login_admin(app, client, email="admin@test.com")
    client.post(f"/api/pops/{pop}/checklists", json={"description": "second"})
    r = client.get("/api/checklists")
    assert r.status_code == 200
    assert [(c["description"], c["userId"]) for c in r.json] == [("second", 2), ("first", 1)]
    login(client)
    assert client.get("/api/checklists").status_code == 403
