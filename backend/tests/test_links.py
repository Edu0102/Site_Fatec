from tests.conftest import give_access, login, login_admin, make_pop, register, run_sql

ADMIN_ROUTES = [("get", "/api/links"), ("post", "/api/links"), ("put", "/api/links/1"),
                ("post", "/api/pop-links"), ("delete", "/api/pops/1/links/1")]
ALL_ROUTES = ADMIN_ROUTES + [("get", "/api/pops/1/links")]
BODY = {"path": "/x", "popId": 1, "linkId": 1}


def test_unauthenticated(client):
    for method, path in ALL_ROUTES:
        assert client.open(path, method=method, json=BODY).status_code == 401


def test_basic_user_is_forbidden_on_admin_routes(client):
    register(client)
    login(client)
    for method, path in ADMIN_ROUTES:
        resp = client.open(path, method=method, json=BODY)
        assert resp.status_code == 403
        assert resp.get_json() == {"error": "Forbidden."}


def test_create_and_list(client):
    login_admin(client.application, client)
    assert client.post("/api/links", json={"path": "  /a  "}).get_json() == {"message": "Link created.", "id": 1}
    client.post("/api/links", json={"path": "/b"})
    rows = client.get("/api/links").get_json()
    assert [(r["id"], r["path"]) for r in rows] == [(1, "/a"), (2, "/b")]
    assert set(rows[0]) == {"id", "path", "createdAtUtc", "updatedAtUtc"}


def test_create_validation(client):
    login_admin(client.application, client)
    for body in ({}, {"path": "   "}, {"path": 123}, {"path": None}, {"path": ["/a"]}):
        resp = client.post("/api/links", json=body)
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "Path is required."}


def test_create_duplicate_path(client):
    login_admin(client.application, client)
    client.post("/api/links", json={"path": "/a"})
    resp = client.post("/api/links", json={"path": "/a"})
    assert resp.status_code == 409
    assert resp.get_json() == {"error": "This link path already exists."}


def test_update(app, client):
    login_admin(app, client)
    client.post("/api/links", json={"path": "/a"})
    run_sql(app, 'UPDATE "Link" SET updated_at_utc = ? WHERE link_id = 1', ("2000-01-01T00:00:00.000000Z",))
    assert client.put("/api/links/1", json={"path": "/new"}).get_json() == {"message": "Link updated."}
    row = client.get("/api/links").get_json()[0]
    assert row["path"] == "/new"
    assert row["updatedAtUtc"] != "2000-01-01T00:00:00.000000Z"


def test_update_errors(client):
    login_admin(client.application, client)
    client.post("/api/links", json={"path": "/a"})
    client.post("/api/links", json={"path": "/b"})
    assert client.put("/api/links/1", json={"path": ""}).get_json() == {"error": "Path is required."}
    resp = client.put("/api/links/999", json={"path": "/z"})
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "Link not found."}
    resp = client.put("/api/links/1", json={"path": "/b"})
    assert resp.status_code == 409
    assert resp.get_json() == {"error": "Another link already has this path."}
    assert client.put("/api/links/1", json={"path": "/a"}).status_code == 200


def test_assign_validation(client):
    login_admin(client.application, client)
    for body in ({}, {"popId": "1", "linkId": 1}, {"popId": True, "linkId": 1}, {"popId": 1}):
        resp = client.post("/api/pop-links", json=body)
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "POP id and link id must be whole numbers."}


def test_assign_errors(app, client):
    login_admin(app, client)
    client.post("/api/links", json={"path": "/a"})
    pop = make_pop(app, creator_id=1)
    resp = client.post("/api/pop-links", json={"popId": pop, "linkId": 999})
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "POP or link not found."}
    assert client.post("/api/pop-links", json={"popId": pop, "linkId": 1}).get_json() == {"message": "Link assigned to POP."}
    resp = client.post("/api/pop-links", json={"popId": pop, "linkId": 1})
    assert resp.status_code == 409
    assert resp.get_json() == {"error": "This link is already assigned to the POP."}


def test_basic_user_sees_only_visible_pop_links(app, client):
    login_admin(app, client)
    client.post("/api/links", json={"path": "/a"})
    client.post("/api/links", json={"path": "/b"})
    pop = make_pop(app, creator_id=1)
    client.post("/api/pop-links", json={"popId": pop, "linkId": 2})
    client.post("/api/pop-links", json={"popId": pop, "linkId": 1})

    basic = app.test_client()
    register(basic, email="basic@test.com")
    login(basic, email="basic@test.com")
    resp = basic.get(f"/api/pops/{pop}/links")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "POP not found or not available."}

    give_access(app, 2, pop)
    rows = basic.get(f"/api/pops/{pop}/links").get_json()
    assert [(r["id"], r["path"]) for r in rows] == [(1, "/a"), (2, "/b")]
    assert set(rows[0]) == {"id", "path", "createdAtUtc", "updatedAtUtc"}


def test_remove_assignment(app, client):
    login_admin(app, client)
    client.post("/api/links", json={"path": "/a"})
    pop = make_pop(app, creator_id=1)
    client.post("/api/pop-links", json={"popId": pop, "linkId": 1})
    assert client.delete(f"/api/pops/{pop}/links/1").get_json() == {"message": "Link removed from POP."}
    resp = client.delete(f"/api/pops/{pop}/links/1")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "This link is not assigned to this POP."}
