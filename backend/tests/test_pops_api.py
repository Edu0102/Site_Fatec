from tests.conftest import give_access, login, login_admin, login_basic, make_pop, register, run_sql, set_user

UNAVAILABLE = {"error": "POP not found or not available."}


def admin_and_basic(app, client):
    # User 1 = admin (not logged in), user 2 = basic (logged in)
    register(client, email="admin@test.com")
    set_user(app, "admin@test.com", user_role="admin")
    login_basic(client, email="basic@test.com", name="Basic")


def test_unauthenticated(client):
    assert client.get("/api/pops").status_code == 401
    assert client.get("/api/pops/1").status_code == 401
    assert client.post("/api/pops", json={"title": "x"}).status_code == 401
    assert client.put("/api/pops/1", json={"title": "x", "status": "draft"}).status_code == 401
    assert client.post("/api/pops/1/archive").status_code == 401


def test_list_follows_visibility(app, client):
    admin_and_basic(app, client)
    shared, hidden, draft = make_pop(app, title="Shared"), make_pop(app, title="Hidden"), make_pop(app, status="draft", title="Draft")
    give_access(app, 2, shared)
    give_access(app, 2, draft)
    assert [p["title"] for p in client.get("/api/pops").json] == ["Shared"]
    login(client, "admin@test.com")
    assert [p["title"] for p in client.get("/api/pops").json] == ["Draft", "Hidden", "Shared"]


def test_get_one(app, client):
    admin_and_basic(app, client)
    shared, hidden = make_pop(app, title="Shared"), make_pop(app)
    give_access(app, 2, shared)
    r = client.get(f"/api/pops/{shared}")
    assert r.status_code == 200
    assert set(r.json) == {"id", "createdBy", "updatedBy", "title", "description", "filePath", "version", "status",
                           "createdAtUtc", "updatedAtUtc"}
    r = client.get(f"/api/pops/{hidden}")
    assert r.status_code == 404 and r.json == UNAVAILABLE


def test_create(app, client):
    login_admin(app, client)
    r = client.post("/api/pops", json={"title": " Receiving ", "description": "Steps", "filePath": "x.pdf", "version": "1.0"})
    assert r.status_code == 200 and r.json == {"message": "POP created.", "id": 1}
    pop = client.get("/api/pops/1").json
    assert pop["title"] == "Receiving" and pop["status"] == "draft" and pop["createdBy"] == 1 and pop["updatedBy"] == 1
    assert pop["description"] == "Steps" and pop["filePath"] == "x.pdf" and pop["version"] == "1.0"
    assert client.post("/api/pops", json={"title": "B", "status": " Published "}).status_code == 200
    assert client.get("/api/pops/2").json["status"] == "published"
    assert client.post("/api/pops", json={"title": "C"}).status_code == 200
    assert client.get("/api/pops/3").json["description"] is None


def test_create_validation_and_permission(app, client):
    login_admin(app, client)
    for body in [{}, {"title": "  "}]:
        r = client.post("/api/pops", json=body)
        assert r.status_code == 400 and r.json == {"error": "Title is required."}
    r = client.post("/api/pops", json={"title": "x", "status": "deleted"})
    assert r.status_code == 400 and r.json == {"error": "Status must be draft, published or archived."}
    login_basic(client, email="b@test.com")
    r = client.post("/api/pops", json={"title": "x"})
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}


def test_update(app, client):
    login_admin(app, client)
    client.post("/api/pops", json={"title": "Old"})
    login_admin(app, client, email="second@test.com", name="Second")
    r = client.put("/api/pops/1", json={"title": "New", "status": "published", "version": "2"})
    assert r.status_code == 200 and r.json == {"message": "POP updated."}
    pop = client.get("/api/pops/1").json
    assert (pop["title"], pop["status"], pop["version"], pop["createdBy"], pop["updatedBy"]) == ("New", "published", "2", 1, 2)
    r = client.put("/api/pops/1", json={"title": "New"})
    assert r.status_code == 400 and r.json == {"error": "Status must be draft, published or archived."}
    r = client.put("/api/pops/999", json={"title": "x", "status": "draft"})
    assert r.status_code == 404 and r.json == {"error": "POP not found."}
    login_basic(client, email="b@test.com")
    assert client.put("/api/pops/1", json={"title": "x", "status": "draft"}).status_code == 403


def test_archive_hides_from_basic(app, client):
    admin_and_basic(app, client)
    pop = make_pop(app)
    give_access(app, 2, pop)
    assert client.post(f"/api/pops/{pop}/archive").status_code == 403
    login(client, "admin@test.com")
    r = client.post(f"/api/pops/{pop}/archive")
    assert r.status_code == 200 and r.json == {"message": "POP archived."}
    assert client.get(f"/api/pops/{pop}").json["status"] == "archived"
    assert client.post("/api/pops/999/archive").status_code == 404
    login(client, "basic@test.com")
    assert client.get(f"/api/pops/{pop}").status_code == 404


def test_inactive_department_stops_access(app, client):
    admin_and_basic(app, client)
    pop = make_pop(app)
    give_access(app, 2, pop)
    assert client.get(f"/api/pops/{pop}").status_code == 200
    run_sql(app, 'UPDATE "Department" SET is_active = 0')
    assert client.get(f"/api/pops/{pop}").status_code == 404
    assert client.get("/api/pops").json == []
    run_sql(app, 'UPDATE "Department" SET is_active = 1')
    assert client.get(f"/api/pops/{pop}").status_code == 200
