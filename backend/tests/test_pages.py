def test_root_serves_portal(client):
    r = client.get("/")
    assert r.status_code == 200 and r.mimetype == "text/html"
    assert b"<html" in r.data.lower()


def test_pages_and_assets_are_served(client):
    for path, mimetype in [("/login.html", "text/html"), ("/html/cadastro.html", "text/html"),
                           ("/css/index.css", "text/css"), ("/js/header.js", "text/javascript")]:
        r = client.get(path)
        assert r.status_code == 200 and r.mimetype == mimetype, path


def test_no_files_outside_wwwroot(client):
    assert client.get("/../backend/app.py").status_code == 404
    assert client.get("/app.py").status_code == 404
    assert client.get("/missing-page.html").status_code == 404
