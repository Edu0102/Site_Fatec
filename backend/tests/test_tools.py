import sqlite3

from tests.conftest import login, login_admin, login_basic, register

TOOL = {"name": "  Calc  ", "description": "d", "url": "https://a.com", "category": "Calculadoras",
        "icon": "bi-calculator"}
KEYS = {"id", "name", "description", "url", "category", "icon", "createdBy", "opens", "lastOpenedAtUtc", "canEdit"}


def other_user(app, email="bia@test.com"):
    # A second logged-in basic user with its own cookies
    c = app.test_client()
    register(c, email=email, name="Bia")
    login(c, email=email)
    return c


def test_unauthenticated(client):
    for method, path in [("get", "/api/tools"), ("post", "/api/tools"), ("put", "/api/tools/1"),
                         ("delete", "/api/tools/1"), ("post", "/api/tools/1/open")]:
        assert client.open(path, method=method, json=TOOL).status_code == 401


def test_create_and_list(client):
    login_basic(client)
    assert client.post("/api/tools", json=TOOL).get_json() == {"message": "Tool created.", "id": 1}
    [row] = client.get("/api/tools").get_json()
    assert set(row) == KEYS
    assert row == {"id": 1, "name": "Calc", "description": "d", "url": "https://a.com", "category": "Calculadoras",
                   "icon": "bi-calculator", "createdBy": 1, "opens": 0, "lastOpenedAtUtc": None, "canEdit": True}


def test_create_validation(client):
    login_basic(client)
    name_err = {"error": "Name is required (max 100 characters)."}
    url_err = {"error": "Enter a valid web address starting with http:// or https://."}
    cases = [({**TOOL, "name": "  "}, name_err), ({**TOOL, "name": "x" * 101}, name_err),
             ({**TOOL, "name": 5}, name_err),
             ({**TOOL, "description": "x" * 121}, {"error": "Description must have at most 120 characters."}),
             ({**TOOL, "category": "x" * 51}, {"error": "Category must have at most 50 characters."}),
             ({**TOOL, "url": "https://" + "a" * 2000}, url_err)]
    cases += [({**TOOL, "url": u}, url_err) for u in ("javascript:alert(1)", "data:text/html,x", "ftp://a", "", 123, "https://", "http:// a.com",
                                                               "https://@", "http://a b", "https:///path",
                                                               "https://a.com/x y", "https://a..com")]
    for body, error in cases:
        resp = client.post("/api/tools", json=body)
        assert resp.status_code == 400, body
        assert resp.get_json() == error, body
        assert client.put("/api/tools/1", json=body).status_code == 400
    assert client.get("/api/tools").get_json() == []


def test_url_scheme_is_case_insensitive(client):
    login_basic(client)
    assert client.post("/api/tools", json={**TOOL, "url": "HTTPS://A.COM"}).status_code == 200


def test_bad_icon_falls_back(client):
    login_basic(client)
    client.post("/api/tools", json={**TOOL, "icon": "x onclick=1"})
    assert client.get("/api/tools").get_json()[0]["icon"] == "bi-tools"


def test_owner_can_update_and_delete(client):
    login_basic(client)
    client.post("/api/tools", json=TOOL)
    assert client.put("/api/tools/1", json={**TOOL, "name": "New"}).get_json() == {"message": "Tool updated."}
    assert client.get("/api/tools").get_json()[0]["name"] == "New"
    assert client.delete("/api/tools/1").get_json() == {"message": "Tool deleted."}
    assert client.get("/api/tools").get_json() == []


def test_other_basic_user_is_forbidden(app, client):
    login_basic(client)
    client.post("/api/tools", json=TOOL)
    bia = other_user(app)
    for resp in (bia.put("/api/tools/1", json={**TOOL, "name": "Hacked"}), bia.delete("/api/tools/1")):
        assert resp.status_code == 403
        assert resp.get_json() == {"error": "Forbidden."}
    [row] = bia.get("/api/tools").get_json()
    assert row["name"] == "Calc" and row["canEdit"] is False


def test_admin_can_update_and_delete_any(app, client):
    login_basic(client)
    client.post("/api/tools", json=TOOL)
    admin = app.test_client()
    login_admin(app, admin, email="adm@test.com")
    assert admin.get("/api/tools").get_json()[0]["canEdit"] is True
    assert admin.put("/api/tools/1", json={**TOOL, "name": "Adm"}).status_code == 200
    assert admin.delete("/api/tools/1").status_code == 200


def test_update_and_delete_missing(client):
    login_basic(client)
    for resp in (client.put("/api/tools/999", json=TOOL), client.delete("/api/tools/999")):
        assert resp.status_code == 404
        assert resp.get_json() == {"error": "Tool not found."}


def test_open_counts_per_user(app, client):
    login_basic(client)
    client.post("/api/tools", json=TOOL)
    bia = other_user(app)
    assert client.post("/api/tools/1/open").get_json() == {"message": "Open recorded."}
    client.post("/api/tools/1/open")
    bia.post("/api/tools/1/open")
    mine = client.get("/api/tools").get_json()[0]
    assert mine["opens"] == 2 and mine["lastOpenedAtUtc"] is not None
    assert bia.get("/api/tools").get_json()[0]["opens"] == 1
    resp = client.post("/api/tools/999/open")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "Tool not found."}


def test_delete_tool_with_usage(app, client):
    login_basic(client)
    client.post("/api/tools", json=TOOL)
    other_user(app).post("/api/tools/1/open")
    assert client.delete("/api/tools/1").status_code == 200
    con = sqlite3.connect(app.config["DATABASE"])
    assert con.execute('SELECT COUNT(*) FROM "ToolUsage"').fetchone() == (0,)
    con.close()


def test_real_addresses_accepted(client):
    login_basic(client)
    for url in ("https://www.gov.br/receitafederal/pt-br?x=1#y", "http://localhost:5000/a", "HTTPS://A.COM",
                "https://acentuação.com.br", "https://sub-dominio.exemplo.com:8443/caminho%20com%20espaco"):
        assert client.post("/api/tools", json={**TOOL, "url": url}).status_code == 200, url
