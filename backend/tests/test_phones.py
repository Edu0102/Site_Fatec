import pytest

from tests.conftest import give_access, login_admin, login_basic, make_pop, run_sql

ADMIN_ROUTES = [
    ("POST", "/api/phones"),
    ("PUT", "/api/phones/1"),
    ("DELETE", "/api/phones/1"),
    ("POST", "/api/pop-phones"),
    ("DELETE", "/api/pops/1/phones/1"),
]
NOT_WHOLE = {"error": "POP id and phone id must be whole numbers."}
MARIA = {"name": " Maria ", "departmentId": 1, "extension": "204", "phoneNumber": "(11) 4000-0000",
         "email": "maria@empresa.com", "tags": ["Matriz"]}


def add_contact(client, name, phone=""):
    return client.post("/api/phones", json={"name": name, "phoneNumber": phone})


def add_department(app, name="Fiscal"):
    return run_sql(app, 'INSERT INTO "Department" (department_name, is_active) VALUES (?, 1)', (name,))


def test_routes_need_login(client):
    for method, path in ADMIN_ROUTES + [("GET", "/api/phones")]:
        assert client.open(path, method=method, json={}).status_code == 401


def test_basic_user_reads_but_cannot_write(client):
    login_basic(client)
    assert client.get("/api/phones").status_code == 200
    for method, path in ADMIN_ROUTES:
        r = client.open(path, method=method, json={})
        assert r.status_code == 403
        assert r.get_json() == {"error": "Forbidden."}


def test_create_and_list_contacts(app, client):
    login_admin(app, client)
    add_department(app)
    assert client.post("/api/phones", json=MARIA).get_json() == {"message": "Contact created.", "id": 1}
    assert add_contact(client, "ana", "(11) 4000-0000").status_code == 200  # same number is fine
    rows = client.get("/api/phones").get_json()
    assert [r["name"] for r in rows] == ["ana", "Maria"]
    maria = rows[1]
    assert set(maria) == {"id", "name", "departmentId", "department", "extension", "phoneNumber", "email", "tags",
                          "createdAtUtc", "updatedAtUtc"}
    assert (maria["departmentId"], maria["department"], maria["extension"], maria["email"], maria["tags"]) == (
        1, "Fiscal", "204", "maria@empresa.com", ["Matriz"])
    assert (rows[0]["departmentId"], rows[0]["department"], rows[0]["email"], rows[0]["tags"]) == (None, None, "", [])
    assert [t["name"] for t in client.get("/api/tags/phone").get_json()] == ["Matriz"]
    assert client.get("/api/tags/link").get_json() == []


def test_bad_department_is_refused(app, client):
    login_admin(app, client)
    for dep, error in ((999, "Department not found."), ("1", "Department id must be a whole number."),
                       (True, "Department id must be a whole number.")):
        r = client.post("/api/phones", json={"name": "Maria", "departmentId": dep})
        assert r.status_code == 400 and r.get_json() == {"error": error}, dep
    assert client.get("/api/phones").get_json() == []
    assert client.post("/api/phones", json={"name": "Maria", "departmentId": None}).status_code == 200


def test_create_validation(app, client):
    login_admin(app, client)
    cases = [({}, "Name is required (max 100 characters)."),
             ({"name": "x" * 101}, "Name is required (max 100 characters)."),
             ({"name": "A", "extension": "1" * 21}, "Extension and phone number must have at most 20 and 30 characters."),
             ({"name": "A", "phoneNumber": "1" * 31}, "Extension and phone number must have at most 20 and 30 characters."),
             ({"name": "A", "email": "maria@"}, "Enter a valid email address."),
             ({"name": "A", "email": "a b@c.com"}, "Enter a valid email address."),
             ({"name": "A", "tags": [1]}, "Tags must be a list of names up to 40 characters (max 20).")]
    for body, error in cases:
        r = client.post("/api/phones", json=body)
        assert r.status_code == 400 and r.get_json() == {"error": error}, body
    assert client.get("/api/phones").get_json() == []


def test_update_contact(app, client):
    login_admin(app, client)
    add_department(app)
    client.post("/api/phones", json=MARIA)
    run_sql(app, 'UPDATE "PhoneNumber" SET updated_at_utc = ? WHERE phone_id = 1', ("2000-01-01T00:00:00.000000Z",))
    body = {"name": "Maria Souza", "departmentId": None, "extension": "", "phoneNumber": "777", "email": "",
            "tags": ["Suporte"]}
    assert client.put("/api/phones/1", json=body).get_json() == {"message": "Contact updated."}
    row = client.get("/api/phones").get_json()[0]
    assert (row["name"], row["department"], row["phoneNumber"], row["tags"]) == ("Maria Souza", None, "777", ["Suporte"])
    assert row["updatedAtUtc"] != "2000-01-01T00:00:00.000000Z"
    r = client.put("/api/phones/99", json=body)
    assert r.status_code == 404 and r.get_json() == {"error": "Contact not found."}
    r = client.put("/api/phones/1", json=dict(body, departmentId=999))
    assert r.status_code == 400 and r.get_json() == {"error": "Department not found."}
    assert client.get("/api/phones").get_json()[0]["tags"] == ["Suporte"]  # failed save changed nothing


def test_delete_contact_in_pop_with_tags(app, client):
    login_admin(app, client)
    add_department(app)
    client.post("/api/phones", json=MARIA)
    make_pop(app)
    client.post("/api/pop-phones", json={"popId": 1, "phoneId": 1})
    assert client.delete("/api/phones/1").get_json() == {"message": "Contact deleted."}
    assert client.get("/api/pops/1/phones").get_json() == []
    assert client.get("/api/phones").get_json() == []
    assert len(client.get("/api/tags/phone").get_json()) == 1
    r = client.delete("/api/phones/1")
    assert r.status_code == 404 and r.get_json() == {"error": "Contact not found."}


def test_pop_phones_follow_pop_visibility(app, client):
    login_admin(app, client)
    pop_id = make_pop(app)
    add_contact(client, "A", "555")
    add_contact(client, "B", "666")
    assert client.post("/api/pop-phones", json={"popId": pop_id, "phoneId": 1}).get_json() == {
        "message": "Phone number assigned to POP."}
    client.post("/api/auth/logout")
    login_basic(client, email="bea@test.com", name="Bea")  # user id 2, no access yet
    r = client.get(f"/api/pops/{pop_id}/phones")
    assert r.status_code == 404
    assert r.get_json() == {"error": "POP not found or not available."}
    give_access(app, 2, pop_id)
    r = client.get(f"/api/pops/{pop_id}/phones")
    assert r.status_code == 200
    assert [(p["id"], p["phoneNumber"]) for p in r.get_json()] == [(1, "555")]


@pytest.mark.parametrize("body", [{"popId": "1", "phoneId": 1}, {"popId": True, "phoneId": 1},
                                  {"phoneId": 1}, {"popId": 1, "phoneId": None}])
def test_assign_requires_whole_numbers(app, client, body):
    login_admin(app, client)
    r = client.post("/api/pop-phones", json=body)
    assert r.status_code == 400
    assert r.get_json() == NOT_WHOLE


def test_assign_unknown_pop_or_phone_is_404(app, client):
    login_admin(app, client)
    make_pop(app)
    add_contact(client, "A", "555")
    r = client.post("/api/pop-phones", json={"popId": 99, "phoneId": 1})
    assert r.status_code == 404
    assert r.get_json() == {"error": "POP or phone number not found."}
    r = client.post("/api/pop-phones", json={"popId": 1, "phoneId": 99})
    assert r.status_code == 404
    assert r.get_json() == {"error": "POP or phone number not found."}


def test_assign_twice_conflicts(app, client):
    login_admin(app, client)
    make_pop(app)
    add_contact(client, "A", "555")
    client.post("/api/pop-phones", json={"popId": 1, "phoneId": 1})
    r = client.post("/api/pop-phones", json={"popId": 1, "phoneId": 1})
    assert r.status_code == 409
    assert r.get_json() == {"error": "This phone number is already assigned to the POP."}


def test_remove_assignment_then_404(app, client):
    login_admin(app, client)
    make_pop(app)
    add_contact(client, "A", "555")
    client.post("/api/pop-phones", json={"popId": 1, "phoneId": 1})
    assert client.delete("/api/pops/1/phones/1").get_json() == {"message": "Phone number removed from POP."}
    r = client.delete("/api/pops/1/phones/1")
    assert r.status_code == 404
    assert r.get_json() == {"error": "This phone number is not assigned to this POP."}
