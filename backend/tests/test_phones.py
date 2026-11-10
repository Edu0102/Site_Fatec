import pytest

from tests.conftest import give_access, login_admin, login_basic, make_pop

ADMIN_ROUTES = [
    ("GET", "/api/phones"),
    ("POST", "/api/phones"),
    ("PUT", "/api/phones/1"),
    ("POST", "/api/pop-phones"),
    ("DELETE", "/api/pops/1/phones/1"),
]
NOT_WHOLE = {"error": "POP id and phone id must be whole numbers."}


def test_admin_routes_need_login(client):
    for method, path in ADMIN_ROUTES:
        assert client.open(path, method=method, json={}).status_code == 401


def test_admin_routes_forbid_basic_user(client):
    login_basic(client)
    for method, path in ADMIN_ROUTES:
        r = client.open(path, method=method, json={})
        assert r.status_code == 403
        assert r.get_json() == {"error": "Forbidden."}


def test_create_and_list_phones(app, client):
    login_admin(app, client)
    assert client.post("/api/phones", json={"phoneNumber": "  555-0101 "}).get_json() == {
        "message": "Phone number created.", "id": 1}
    client.post("/api/phones", json={"phoneNumber": "555-0202"})
    phones = client.get("/api/phones").get_json()
    assert [p["id"] for p in phones] == [1, 2]
    assert [p["phoneNumber"] for p in phones] == ["555-0101", "555-0202"]
    assert set(phones[0]) == {"id", "phoneNumber", "createdAtUtc", "updatedAtUtc"}


@pytest.mark.parametrize("body", [{}, {"phoneNumber": ""}, {"phoneNumber": "   "}, {"phoneNumber": 5}, {"phoneNumber": None}])
def test_create_requires_phone_number(app, client, body):
    login_admin(app, client)
    r = client.post("/api/phones", json=body)
    assert r.status_code == 400
    assert r.get_json() == {"error": "Phone number is required."}


def test_create_duplicate_conflicts(app, client):
    login_admin(app, client)
    client.post("/api/phones", json={"phoneNumber": "555"})
    r = client.post("/api/phones", json={"phoneNumber": " 555 "})
    assert r.status_code == 409
    assert r.get_json() == {"error": "This phone number already exists."}


def test_update_changes_number_and_timestamp(app, client):
    login_admin(app, client)
    client.post("/api/phones", json={"phoneNumber": "555"})
    before = client.get("/api/phones").get_json()[0]
    assert client.put("/api/phones/1", json={"phoneNumber": "777"}).get_json() == {"message": "Phone number updated."}
    after = client.get("/api/phones").get_json()[0]
    assert after["phoneNumber"] == "777"
    assert after["updatedAtUtc"] != before["updatedAtUtc"]


def test_update_errors(app, client):
    login_admin(app, client)
    client.post("/api/phones", json={"phoneNumber": "555"})
    client.post("/api/phones", json={"phoneNumber": "666"})
    r = client.put("/api/phones/1", json={"phoneNumber": " "})
    assert r.status_code == 400
    assert r.get_json() == {"error": "Phone number is required."}
    r = client.put("/api/phones/99", json={"phoneNumber": "777"})
    assert r.status_code == 404
    assert r.get_json() == {"error": "Phone number not found."}
    r = client.put("/api/phones/1", json={"phoneNumber": "666"})
    assert r.status_code == 409
    assert r.get_json() == {"error": "This phone number already exists."}


def test_pop_phones_follow_pop_visibility(app, client):
    login_admin(app, client)
    pop_id = make_pop(app)
    client.post("/api/phones", json={"phoneNumber": "555"})
    client.post("/api/phones", json={"phoneNumber": "666"})
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
    client.post("/api/phones", json={"phoneNumber": "555"})
    r = client.post("/api/pop-phones", json={"popId": 99, "phoneId": 1})
    assert r.status_code == 404
    assert r.get_json() == {"error": "POP or phone number not found."}
    r = client.post("/api/pop-phones", json={"popId": 1, "phoneId": 99})
    assert r.status_code == 404
    assert r.get_json() == {"error": "POP or phone number not found."}


def test_assign_twice_conflicts(app, client):
    login_admin(app, client)
    make_pop(app)
    client.post("/api/phones", json={"phoneNumber": "555"})
    client.post("/api/pop-phones", json={"popId": 1, "phoneId": 1})
    r = client.post("/api/pop-phones", json={"popId": 1, "phoneId": 1})
    assert r.status_code == 409
    assert r.get_json() == {"error": "This phone number is already assigned to the POP."}


def test_remove_assignment_then_404(app, client):
    login_admin(app, client)
    make_pop(app)
    client.post("/api/phones", json={"phoneNumber": "555"})
    client.post("/api/pop-phones", json={"popId": 1, "phoneId": 1})
    assert client.delete("/api/pops/1/phones/1").get_json() == {"message": "Phone number removed from POP."}
    r = client.delete("/api/pops/1/phones/1")
    assert r.status_code == 404
    assert r.get_json() == {"error": "This phone number is not assigned to this POP."}
