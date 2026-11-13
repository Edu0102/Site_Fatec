from repositories import tags
from routes import json_tags
from tests.conftest import login_admin, login_basic, run_sql


def test_unauthenticated(client):
    for method, path in [("get", "/api/tags/link"), ("post", "/api/tags/link"), ("delete", "/api/tags/1")]:
        assert client.open(path, method=method, json={"name": "x"}).status_code == 401


def test_basic_user_reads_but_cannot_write(app, client):
    run_sql(app, 'INSERT INTO "Tag" (tag_scope, tag_name) VALUES (?, ?)', ("link", "Federal"))
    login_basic(client)
    assert client.get("/api/tags/link").get_json() == [{"id": 1, "name": "Federal"}]
    assert client.post("/api/tags/link", json={"name": "x"}).status_code == 403
    assert client.delete("/api/tags/1").status_code == 403


def test_unknown_scope(client):
    login_basic(client)
    assert client.get("/api/tags/other").status_code == 404


def test_create_list_sorted_and_scoped(client):
    login_admin(client.application, client)
    assert client.post("/api/tags/link", json={"name": " Federal "}).get_json() == {"message": "Filter created.", "id": 1}
    client.post("/api/tags/link", json={"name": "Débitos"})
    assert client.get("/api/tags/link").get_json() == [{"id": 2, "name": "Débitos"}, {"id": 1, "name": "Federal"}]
    resp = client.post("/api/tags/link", json={"name": "federal"})
    assert resp.status_code == 409 and resp.get_json() == {"error": "This filter already exists."}
    assert client.post("/api/tags/phone", json={"name": "Federal"}).status_code == 200
    assert client.get("/api/tags/phone").get_json() == [{"id": 3, "name": "Federal"}]


def test_create_validation(client):
    login_admin(client.application, client)
    for body in ({}, {"name": "  "}, {"name": "x" * 41}, {"name": 123}):
        resp = client.post("/api/tags/link", json=body)
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "Filter name is required (max 40 characters)."}


def test_delete_removes_item_links(app, client):
    login_admin(app, client)
    client.post("/api/tags/link", json={"name": "Federal"})
    run_sql(app, 'INSERT INTO "Link" (link_title, link_path) VALUES (?, ?)', ("A", "https://a.com"))
    run_sql(app, 'INSERT INTO "LinkTag" (link_id, tag_id) VALUES (1, 1)')
    assert client.delete("/api/tags/1").get_json() == {"message": "Filter deleted."}
    assert client.get("/api/tags/link").get_json() == []
    with app.app_context():
        assert tags.names_for("link", [1]) == {}
    resp = client.delete("/api/tags/1")
    assert resp.status_code == 404 and resp.get_json() == {"error": "Filter not found."}


def test_set_for_reuses_existing_tag_ignoring_case(app):
    run_sql(app, 'INSERT INTO "Tag" (tag_scope, tag_name) VALUES (?, ?)', ("link", "Federal"))
    run_sql(app, 'INSERT INTO "Link" (link_title, link_path) VALUES (?, ?)', ("A", "https://a.com"))
    with app.app_context():
        tags.set_for("link", 1, ["federal", "Estadual"])
        assert tags.names_for("link", [1]) == {1: ["Estadual", "Federal"]}
        tags.set_for("link", 1, ["Estadual"])  # replaces, doesn't add
        assert tags.names_for("link", [1]) == {1: ["Estadual"]}
        assert [t["name"] for t in tags.get_all("link")] == ["Estadual", "Federal"]
        assert tags.get_all("phone") == []


def test_json_tags(app):
    cases = [({"tags": [" A ", "a", "", "B"]}, ["A", "B"]), ({}, []), ({"tags": "A"}, None), ({"tags": [1]}, None),
             ({"tags": ["x" * 41]}, None), ({"tags": [str(i) for i in range(21)]}, None)]
    for body, expected in cases:
        with app.test_request_context(json=body):
            assert json_tags() == expected, body


def test_lone_surrogate_tag_is_refused(client):
    login_admin(client.application, client)
    raw = b'{"title": "A", "url": "https://a.com", "tags": ["\\ud800"]}'  # JSON escape for a lone surrogate
    resp = client.post("/api/links", data=raw, content_type="application/json")
    assert resp.status_code == 400
