from tests.conftest import give_access, login, login_admin, login_basic, make_pop, register

SELF = {"error": "You can't change your own role or active status."}


# ---------- PUT /api/users/{id} ----------

def two_users(app, client):
    # Admin (user 1, logged in) and basic user 2 (bia@test.com, not logged in)
    login_admin(app, client)
    register(client, email="bia@test.com", name="Bia")


def test_user_edit_needs_admin(app, client):
    assert client.put("/api/users/1", json={"role": "admin"}).status_code == 401
    login_basic(client)
    r = client.put("/api/users/1", json={"role": "admin"})
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}


def test_promote_applies_at_once(app, client):
    two_users(app, client)
    bia = app.test_client()
    login(bia, "bia@test.com")
    r = client.put("/api/users/2", json={"role": "admin"})
    assert r.status_code == 200 and r.json == {"message": "User updated."}
    assert bia.get("/api/auth/me").json["role"] == "admin"


def test_deactivate_ends_sessions_and_login(app, client):
    two_users(app, client)
    bia = app.test_client()
    login(bia, "bia@test.com")
    assert client.put("/api/users/2", json={"isActive": False}).status_code == 200
    assert bia.get("/api/auth/me").status_code == 401
    assert login(bia, "bia@test.com").status_code == 401
    client.put("/api/users/2", json={"isActive": True})
    assert login(bia, "bia@test.com").status_code == 200


def test_new_password_ends_sessions(app, client):
    two_users(app, client)
    bia = app.test_client()
    login(bia, "bia@test.com")
    assert client.put("/api/users/2", json={"password": "brand-new-pass"}).status_code == 200
    assert bia.get("/api/auth/me").status_code == 401
    assert login(bia, "bia@test.com").status_code == 401
    assert login(bia, "bia@test.com", "brand-new-pass").status_code == 200


def test_user_edit_validation(app, client):
    two_users(app, client)
    cases = [
        ({}, 400, {"error": "Nothing to change."}),
        ({"role": "boss"}, 400, {"error": "Role must be admin or basic."}),
        ({"isActive": "no"}, 400, {"error": "isActive must be true or false."}),
        ({"password": "short"}, 400, {"error": "Password must have at least 8 characters."}),
    ]
    for body, status, expected in cases:
        r = client.put("/api/users/2", json=body)
        assert (r.status_code, r.json) == (status, expected)
    r = client.put("/api/users/999", json={"role": "basic"})
    assert r.status_code == 404 and r.json == {"error": "User not found."}


def test_admin_cant_lock_themselves_out(app, client):
    two_users(app, client)
    for body in [{"role": "basic"}, {"isActive": False}]:
        r = client.put("/api/users/1", json=body)
        assert r.status_code == 409 and r.json == SELF
    assert client.put("/api/users/1", json={"password": "my-new-password"}).status_code == 200


# ---------- PUT /api/departments/{id} ----------

def test_department_edit(app, client):
    login_admin(app, client)
    client.post("/api/departments", json={"name": "IT", "code": "TI"})
    client.post("/api/departments", json={"name": "Fiscal", "code": "FS"})
    r = client.put("/api/departments/1", json={"name": " Tech ", "code": " tec ", "isActive": False})
    assert r.status_code == 200 and r.json == {"message": "Department updated."}
    assert client.get("/api/departments").json[0] == {"id": 1, "name": "Tech", "code": "TEC", "isActive": False}
    r = client.put("/api/departments/1", json={"name": "Tech", "code": "fs", "isActive": True})
    assert r.status_code == 409 and r.json == {"error": "This department code already exists."}
    r = client.put("/api/departments/1", json={"name": " ", "code": "X", "isActive": True})
    assert r.status_code == 400 and r.json == {"error": "Name and code are required."}
    r = client.put("/api/departments/1", json={"name": "A", "code": "X"})
    assert r.status_code == 400 and r.json == {"error": "isActive must be true or false."}
    r = client.put("/api/departments/999", json={"name": "A", "code": "X", "isActive": True})
    assert r.status_code == 404 and r.json == {"error": "Department not found."}
    login_basic(client, email="b@test.com")
    assert client.put("/api/departments/1", json={"name": "A", "code": "X", "isActive": True}).status_code == 403


# ---------- PUT / DELETE /api/standard-checks/{id} ----------

def pop_with_checks(app, client):
    # Admin logged in; a published POP with checks 1 ("First") and 2 ("Second")
    login_admin(app, client)
    pop = make_pop(app)
    client.post(f"/api/pops/{pop}/standard-checks", json={"checkText": "First", "checkOrder": 1})
    client.post(f"/api/pops/{pop}/standard-checks", json={"checkText": "Second", "checkOrder": 2})
    return pop


def test_check_edit(app, client):
    pop = pop_with_checks(app, client)
    r = client.put("/api/standard-checks/1", json={"checkText": " Fixed ", "checkOrder": 5})
    assert r.status_code == 200 and r.json == {"message": "Standard check updated."}
    assert [c["checkText"] for c in client.get(f"/api/pops/{pop}/standard-checks").json] == ["Second", "Fixed"]
    r = client.put("/api/standard-checks/1", json={"checkText": "", "checkOrder": 1})
    assert r.status_code == 400 and r.json == {"error": "Check text is required."}
    r = client.put("/api/standard-checks/1", json={"checkText": "x", "checkOrder": "1"})
    assert r.status_code == 400 and r.json == {"error": "Check order must be a whole number."}
    r = client.put("/api/standard-checks/999", json={"checkText": "x", "checkOrder": 1})
    assert r.status_code == 404 and r.json == {"error": "Standard check not found."}
    login_basic(client, email="b@test.com")
    assert client.put("/api/standard-checks/1", json={"checkText": "x", "checkOrder": 1}).status_code == 403


def test_check_delete_removes_its_ticks(app, client):
    pop = pop_with_checks(app, client)
    client.post(f"/api/pops/{pop}/checklists", json={})
    r = client.delete("/api/standard-checks/1")
    assert r.status_code == 200 and r.json == {"message": "Standard check deleted."}
    assert [i["checkText"] for i in client.get("/api/checklists/1").json["items"]] == ["Second"]
    assert client.delete("/api/standard-checks/1").status_code == 404
    login_basic(client, email="b@test.com")
    assert client.delete("/api/standard-checks/2").status_code == 403


# ---------- DELETE /api/checklists/{id} ----------

def test_checklist_delete(app, client):
    register(client)
    pop = make_pop(app)
    give_access(app, 1, pop)
    login(client)
    client.post(f"/api/pops/{pop}/checklists", json={})
    client.post(f"/api/pops/{pop}/checklists", json={})
    r = client.delete("/api/checklists/1")
    assert r.status_code == 200 and r.json == {"message": "Checklist deleted."}
    assert client.get("/api/checklists/1").status_code == 404
    client.post("/api/checklists/2/complete")
    r = client.delete("/api/checklists/2")
    assert r.status_code == 409 and r.json == {"error": "This checklist is already completed."}
    r = client.delete("/api/checklists/999")
    assert r.status_code == 404 and r.json == {"error": "Checklist not found."}
    client.post(f"/api/pops/{pop}/checklists", json={})
    login_admin(app, client, email="admin@test.com")
    assert client.delete("/api/checklists/3").status_code == 404  # only the owner deletes


# ---------- name and email ----------

def test_admin_edits_name_and_email(app, client):
    two_users(app, client)
    r = client.put("/api/users/2", json={"name": "  Beatriz ", "email": " BEA@test.com "})
    assert r.status_code == 200 and r.json == {"message": "User updated."}
    bia = [u for u in client.get("/api/admin/users").json if u["id"] == 2][0]
    assert (bia["name"], bia["email"]) == ("Beatriz", "bea@test.com")
    assert login(app.test_client(), "bea@test.com").status_code == 200


def test_edit_validation(app, client):
    two_users(app, client)
    for body, error in [({"name": "  "}, "Name can't be empty."), ({"email": " "}, "Enter a valid email."),
                        ({"email": "abc"}, "Enter a valid email."), ({"name": 5}, "Name can't be empty.")]:
        r = client.put("/api/users/2", json=body)
        assert r.status_code == 400 and r.json == {"error": error}, body


def test_edit_email_conflict(app, client):
    two_users(app, client)
    r = client.put("/api/users/1", json={"email": " BIA@test.com "})
    assert r.status_code == 409 and r.json == {"error": "This email is already registered."}
    emails = sorted(u["email"] for u in client.get("/api/admin/users").json)
    assert emails == ["ana@test.com", "bia@test.com"]


def test_edit_missing_user(app, client):
    two_users(app, client)
    r = client.put("/api/users/999", json={"name": "X"})
    assert r.status_code == 404 and r.json == {"error": "User not found."}


def test_basic_cannot_edit_profile(app, client):
    login_basic(client)
    assert client.put("/api/users/1", json={"name": "X"}).status_code == 403
