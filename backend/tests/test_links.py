from tests.conftest import give_access, login, login_admin, make_pop, register, run_sql

ADMIN_ROUTES = [("post", "/api/links"), ("put", "/api/links/1"), ("delete", "/api/links/1"),
                ("post", "/api/pop-links"), ("delete", "/api/pops/1/links/1")]
ALL_ROUTES = ADMIN_ROUTES + [("get", "/api/links"), ("get", "/api/pops/1/links")]
BODY = {"title": "A", "url": "https://a.com", "popId": 1, "linkId": 1}
RECEITA = {"title": "  Receita  ", "url": "https://www.gov.br/receitafederal/", "description": "d", "subject": "Cadastral",
           "tags": ["Federal", "Consulta Pública"]}
URL_ERROR = {"error": "Enter a valid web address starting with http:// or https://."}


def add_link(client, title, url):
    return client.post("/api/links", json={"title": title, "url": url})


def test_unauthenticated(client):
    for method, path in ALL_ROUTES:
        assert client.open(path, method=method, json=BODY).status_code == 401


def test_basic_user_reads_but_cannot_write(client):
    register(client)
    login(client)
    assert client.get("/api/links").status_code == 200
    for method, path in ADMIN_ROUTES:
        resp = client.open(path, method=method, json=BODY)
        assert resp.status_code == 403
        assert resp.get_json() == {"error": "Forbidden."}


def test_create_and_list(client):
    login_admin(client.application, client)
    assert client.post("/api/links", json=RECEITA).get_json() == {"message": "Link created.", "id": 1}
    add_link(client, "abc", "http://b.com")
    rows = client.get("/api/links").get_json()
    assert [r["title"] for r in rows] == ["abc", "Receita"]  # by title, ignoring case
    receita = rows[1]
    assert set(receita) == {"id", "title", "description", "url", "subject", "tags", "createdAtUtc", "updatedAtUtc"}
    assert (receita["url"], receita["description"], receita["subject"]) == ("https://www.gov.br/receitafederal/", "d", "Cadastral")
    assert receita["tags"] == ["Consulta Pública", "Federal"]
    assert rows[0]["tags"] == [] and rows[0]["description"] == ""
    assert [t["name"] for t in client.get("/api/tags/link").get_json()] == ["Consulta Pública", "Federal"]


def test_bad_urls_are_refused(client):
    login_admin(client.application, client)
    for url in ("javascript:alert(1)", "http://a b", "www.gov.br", "", None):
        resp = client.post("/api/links", json={"title": "A", "url": url})
        assert resp.status_code == 400 and resp.get_json() == URL_ERROR, url
    assert client.get("/api/links").get_json() == []


def test_create_validation(client):
    login_admin(client.application, client)
    cases = [({"url": "https://a.com"}, "Title is required (max 150 characters)."),
             ({"title": "x" * 151, "url": "https://a.com"}, "Title is required (max 150 characters)."),
             ({"title": "A", "url": "https://a.com", "description": "x" * 501}, "Description must have at most 500 characters."),
             ({"title": "A", "url": "https://a.com", "subject": "x" * 101}, "Subject must have at most 100 characters."),
             ({"title": "A", "url": "https://a.com", "tags": "Federal"}, "Tags must be a list of names up to 40 characters (max 20).")]
    for body, error in cases:
        resp = client.post("/api/links", json=body)
        assert resp.status_code == 400 and resp.get_json() == {"error": error}
    assert client.get("/api/links").get_json() == []


def test_duplicate_url(client):
    login_admin(client.application, client)
    add_link(client, "A", "https://a.com")
    add_link(client, "B", "https://b.com")
    conflict = {"error": "A link with this address already exists."}
    resp = add_link(client, "C", "https://a.com")
    assert resp.status_code == 409 and resp.get_json() == conflict
    resp = client.put("/api/links/2", json={"title": "B", "url": "https://a.com", "tags": ["Nova"]})
    assert resp.status_code == 409 and resp.get_json() == conflict
    assert client.get("/api/tags/link").get_json() == []  # the failed save left nothing behind
    assert len(client.get("/api/links").get_json()) == 2


def test_update(app, client):
    login_admin(app, client)
    client.post("/api/links", json=dict(RECEITA, tags=["Federal"]))
    run_sql(app, 'UPDATE "Link" SET updated_at_utc = ? WHERE link_id = 1', ("2000-01-01T00:00:00.000000Z",))
    body = {"title": "Sefaz", "url": "https://sefaz.sp.gov.br", "description": "", "subject": "ICMS", "tags": ["Estadual"]}
    assert client.put("/api/links/1", json=body).get_json() == {"message": "Link updated."}
    row = client.get("/api/links").get_json()[0]
    assert (row["title"], row["url"], row["subject"], row["tags"]) == ("Sefaz", "https://sefaz.sp.gov.br", "ICMS", ["Estadual"])
    assert row["updatedAtUtc"] != "2000-01-01T00:00:00.000000Z"
    resp = client.put("/api/links/999", json=body)
    assert resp.status_code == 404 and resp.get_json() == {"error": "Link not found."}
    assert client.put("/api/links/1", json={"title": "", "url": "https://a.com"}).status_code == 400


def test_delete_link_in_pop_with_tags(app, client):
    login_admin(app, client)
    client.post("/api/links", json=RECEITA)
    pop = make_pop(app, creator_id=1)
    client.post("/api/pop-links", json={"popId": pop, "linkId": 1})
    assert client.delete("/api/links/1").get_json() == {"message": "Link deleted."}
    assert client.get(f"/api/pops/{pop}/links").get_json() == []
    assert client.get("/api/links").get_json() == []
    assert len(client.get("/api/tags/link").get_json()) == 2  # filters stay
    resp = client.delete("/api/links/1")
    assert resp.status_code == 404 and resp.get_json() == {"error": "Link not found."}


def test_assign_validation(client):
    login_admin(client.application, client)
    for body in ({}, {"popId": "1", "linkId": 1}, {"popId": True, "linkId": 1}, {"popId": 1}):
        resp = client.post("/api/pop-links", json=body)
        assert resp.status_code == 400
        assert resp.get_json() == {"error": "POP id and link id must be whole numbers."}


def test_assign_errors(app, client):
    login_admin(app, client)
    add_link(client, "A", "https://a.com")
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
    add_link(client, "B", "https://b.com")
    client.post("/api/links", json=dict(RECEITA, title="A", url="https://a.com"))
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
    assert [(r["id"], r["title"]) for r in rows] == [(2, "A"), (1, "B")]
    assert rows[0]["tags"] == ["Consulta Pública", "Federal"]


def test_remove_assignment(app, client):
    login_admin(app, client)
    add_link(client, "A", "https://a.com")
    pop = make_pop(app, creator_id=1)
    client.post("/api/pop-links", json={"popId": pop, "linkId": 1})
    assert client.delete(f"/api/pops/{pop}/links/1").get_json() == {"message": "Link removed from POP."}
    resp = client.delete(f"/api/pops/{pop}/links/1")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "This link is not assigned to this POP."}
