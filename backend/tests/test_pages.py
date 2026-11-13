def test_root_serves_portal(client):
    r = client.get("/")
    assert r.status_code == 200 and r.mimetype == "text/html"
    assert b"<html" in r.data.lower()


def test_pages_and_assets_are_served(client):
    for path, mimetype in [("/login.html", "text/html"), ("/html/ferramentas.html", "text/html"), ("/html/colaboradores.html", "text/html"),
                           ("/css/style.css", "text/css"), ("/js/header.js", "text/javascript"),
                           ("/js/api.js", "text/javascript"), ("/js/centrallink-api.js", "text/javascript"),
                           ("/js/listatelefonica-api.js", "text/javascript"), ("/html/centrallink.html", "text/html"),
                           ("/html/listatelefonica.html", "text/html"),("/assets/Logo.svg", "image/svg+xml")]:
        r = client.get(path)
        assert r.status_code == 200 and r.mimetype == mimetype, path


def test_no_files_outside_wwwroot(client):
    assert client.get("/../backend/app.py").status_code == 404
    assert client.get("/app.py").status_code == 404
    assert client.get("/missing-page.html").status_code == 404


def test_old_pages_are_gone(client):
    for path in ("/html/guia.html", "/html/abaguia.html", "/html/cadastro.html", "/html/funcionarios.html"):
        assert client.get(path).status_code == 404, path
