import io

from tests.conftest import login, register, set_user

PNG = b"\x89PNG\r\n\x1a\n" + b"png-body"
JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-body"
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"webp-body"
TOO_BIG = {"error": "Photo must be at most 2 MB."}


def upload(client, data, name="me.png"):
    # PUT /me/photo as a browser form with one file field
    return client.put("/me/photo", data={"photo": (io.BytesIO(data), name)}, content_type="multipart/form-data")


def test_unauthenticated(client):
    assert upload(client, PNG).status_code == 401
    assert client.get("/users/1/photo").status_code == 401
    assert client.delete("/me/photo").status_code == 401
    assert client.delete("/users/1/photo").status_code == 401


def test_upload_and_read(client):
    register(client)
    login(client)
    r = upload(client, PNG)
    assert r.status_code == 200 and r.json == {"message": "Photo saved."}
    r = client.get("/users/1/photo")
    assert r.status_code == 200 and r.data == PNG and r.mimetype == "image/png"
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_replace_photo(client):
    register(client)
    login(client)
    upload(client, PNG)
    assert upload(client, JPEG, "me.jpg").status_code == 200
    r = client.get("/users/1/photo")
    assert r.data == JPEG and r.mimetype == "image/jpeg"
    assert upload(client, WEBP, "me.webp").status_code == 200
    assert client.get("/users/1/photo").mimetype == "image/webp"


def test_type_comes_from_bytes_not_name(client):
    register(client)
    login(client)
    r = upload(client, b"<script>alert(1)</script>", "evil.png")
    assert r.status_code == 400 and r.json == {"error": "Photo must be a JPEG, PNG or WebP image."}
    r = upload(client, b"", "empty.png")
    assert r.status_code == 400


def test_missing_file(client):
    register(client)
    login(client)
    r = client.put("/me/photo", data={}, content_type="multipart/form-data")
    assert r.status_code == 400 and r.json == {"error": "Photo is required."}
    r = client.put("/me/photo", json={"photo": "abc"})
    assert r.status_code == 400 and r.json == {"error": "Photo is required."}


def test_size_limit(client):
    register(client)
    login(client)
    exact = PNG + b"\x00" * (2 * 1024 * 1024 - len(PNG))
    assert upload(client, exact).status_code == 200
    r = upload(client, exact + b"\x00")
    assert r.status_code == 413 and r.json == TOO_BIG
    r = upload(client, exact * 2)  # bigger than the whole request limit
    assert r.status_code == 413 and r.json == TOO_BIG


def test_delete_own(client):
    register(client)
    login(client)
    r = client.delete("/me/photo")
    assert r.status_code == 404 and r.json == {"error": "Photo not found."}
    upload(client, PNG)
    r = client.delete("/me/photo")
    assert r.status_code == 200 and r.json == {"message": "Photo deleted."}
    assert client.get("/users/1/photo").status_code == 404


def test_others_can_see_but_only_admin_deletes(app, client):
    register(client)
    login(client)
    upload(client, PNG)
    register(client, email="b@test.com", name="Bia")
    login(client, email="b@test.com")
    assert client.get("/users/1/photo").data == PNG
    r = client.delete("/users/1/photo")
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}
    set_user(app, "b@test.com", user_role="admin")
    r = client.delete("/users/1/photo")
    assert r.status_code == 200 and r.json == {"message": "Photo deleted."}
    assert client.delete("/users/1/photo").status_code == 404
