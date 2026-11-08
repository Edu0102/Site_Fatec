from tests.conftest import give_access, login, make_pop, register, run_sql, set_user


def add_check(app, pop_id, text, order):
    # Insert a standard check directly; returns its id
    return run_sql(app, 'INSERT INTO "StandardCheck" (pop_id, check_text, check_order) VALUES (?, ?, ?)', (pop_id, text, order))


def setup_pop(app, client):
    # User 1 (basic, logged in) with access to a published POP that has two checks
    register(client)
    pop = make_pop(app)
    give_access(app, 1, pop)
    c2 = add_check(app, pop, "Second", 2)
    c1 = add_check(app, pop, "First", 1)
    login(client)
    return pop, c1, c2


def test_unauthenticated(client):
    assert client.post("/api/pops/1/checklists", json={}).status_code == 401
    assert client.get("/api/checklists/1").status_code == 401
    assert client.get("/api/me/checklists").status_code == 401
    assert client.put("/api/checklists/1/items/1", json={"isChecked": True}).status_code == 401
    assert client.post("/api/checklists/1/complete").status_code == 401


def test_create_makes_unchecked_items(app, client):
    pop, c1, c2 = setup_pop(app, client)
    r = client.post(f"/api/pops/{pop}/checklists", json={"description": "  Morning run "})
    assert r.status_code == 200 and r.json == {"message": "Checklist created.", "id": 1}
    body = client.get("/api/checklists/1").json
    assert body["id"] == 1 and body["popId"] == pop and body["userId"] == 1
    assert body["description"] == "Morning run" and body["completedAtUtc"] is None and body["createdAtUtc"]
    assert body["items"] == [
        {"standardCheckId": c1, "checkText": "First", "checkOrder": 1, "isChecked": False},
        {"standardCheckId": c2, "checkText": "Second", "checkOrder": 2, "isChecked": False},
    ]


def test_create_needs_visible_pop(app, client):
    register(client)
    login(client)
    hidden, draft = make_pop(app), make_pop(app, status="draft")
    give_access(app, 1, draft)
    for pop in (hidden, draft, 999):
        r = client.post(f"/api/pops/{pop}/checklists", json={})
        assert r.status_code == 404 and r.json == {"error": "POP not found or not available."}


def test_admin_can_start_on_any_pop(app, client):
    register(client)
    set_user(app, "ana@test.com", user_role="admin")
    login(client)
    pop = make_pop(app, status="draft")
    assert client.post(f"/api/pops/{pop}/checklists", json={}).status_code == 200
    assert client.get("/api/checklists/1").json["description"] is None


def test_only_owner_or_admin_can_read(app, client):
    pop, _, _ = setup_pop(app, client)
    client.post(f"/api/pops/{pop}/checklists", json={})
    register(client, email="b@test.com")
    login(client, email="b@test.com")
    r = client.get("/api/checklists/1")
    assert r.status_code == 404 and r.json == {"error": "Checklist not found."}
    assert client.get("/api/me/checklists").json == []
    set_user(app, "b@test.com", user_role="admin")
    login(client, email="b@test.com")
    assert client.get("/api/checklists/1").status_code == 200


def test_my_checklists(app, client):
    pop, _, _ = setup_pop(app, client)
    client.post(f"/api/pops/{pop}/checklists", json={"description": "a"})
    client.post(f"/api/pops/{pop}/checklists", json={"description": "b"})
    r = client.get("/api/me/checklists")
    assert r.status_code == 200 and [c["description"] for c in r.json] == ["b", "a"]
    assert set(r.json[0]) == {"id", "popId", "userId", "description", "createdAtUtc", "completedAtUtc"}


def test_tick_item(app, client):
    pop, c1, _ = setup_pop(app, client)
    client.post(f"/api/pops/{pop}/checklists", json={})
    r = client.put(f"/api/checklists/1/items/{c1}", json={"isChecked": True})
    assert r.status_code == 200 and r.json == {"message": "Checklist item updated."}
    assert client.get("/api/checklists/1").json["items"][0]["isChecked"] is True
    client.put(f"/api/checklists/1/items/{c1}", json={"isChecked": False})
    assert client.get("/api/checklists/1").json["items"][0]["isChecked"] is False


def test_tick_item_errors(app, client):
    pop, c1, _ = setup_pop(app, client)
    client.post(f"/api/pops/{pop}/checklists", json={})
    for bad in [{}, {"isChecked": 1}, {"isChecked": "true"}]:
        r = client.put(f"/api/checklists/1/items/{c1}", json=bad)
        assert r.status_code == 400 and r.json == {"error": "isChecked must be true or false."}
    for url in ["/api/checklists/1/items/999", f"/api/checklists/999/items/{c1}"]:
        r = client.put(url, json={"isChecked": True})
        assert r.status_code == 404 and r.json == {"error": "Checklist item not found."}
    register(client, email="b@test.com")
    login(client, email="b@test.com")
    assert client.put(f"/api/checklists/1/items/{c1}", json={"isChecked": True}).status_code == 404


def test_complete(app, client):
    pop, c1, _ = setup_pop(app, client)
    client.post(f"/api/pops/{pop}/checklists", json={})
    r = client.post("/api/checklists/1/complete")
    assert r.status_code == 200 and r.json == {"message": "Checklist completed."}
    assert client.get("/api/checklists/1").json["completedAtUtc"]
    r = client.post("/api/checklists/1/complete")
    assert r.status_code == 409 and r.json == {"error": "This checklist is already completed."}
    r = client.put(f"/api/checklists/1/items/{c1}", json={"isChecked": True})
    assert r.status_code == 409 and r.json == {"error": "This checklist is already completed."}
    r = client.post("/api/checklists/999/complete")
    assert r.status_code == 404 and r.json == {"error": "Checklist not found."}
    register(client, email="b@test.com")
    login(client, email="b@test.com")
    assert client.post("/api/checklists/1/complete").status_code == 404
