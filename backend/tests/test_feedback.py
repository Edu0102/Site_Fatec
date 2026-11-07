import pytest

from tests.conftest import give_access, login, login_admin, login_basic, make_pop, set_user


def send(client, description="Slow page", **extra):
    # POST /feedback with a description and optional extra fields
    return client.post("/feedback", json={"description": description, **extra})


def test_unauthenticated(client):
    assert client.post("/feedback", json={"description": "x"}).status_code == 401
    assert client.get("/feedback").status_code == 401
    assert client.post("/feedback/1/answer", json={"answer": "x"}).status_code == 401
    assert client.post("/feedback/1/close").status_code == 401


def test_send_without_pop(client):
    login_basic(client)
    r = send(client, "  Slow page  ")
    assert r.status_code == 200 and r.json == {"message": "Feedback sent.", "id": 1}
    items = client.get("/feedback").json
    assert len(items) == 1
    item = items[0]
    assert item["id"] == 1 and item["userId"] == 1 and item["description"] == "Slow page"
    assert item["popId"] is None and item["status"] == "open" and item["answer"] is None
    assert item["answeredBy"] is None and item["answeredAtUtc"] is None and item["createdAtUtc"]
    assert send(client, "null pop", popId=None).status_code == 200


def test_send_with_visible_pop(app, client):
    login_basic(client)
    pop = make_pop(app)
    give_access(app, 1, pop)
    assert send(client, popId=pop).status_code == 200
    assert client.get("/feedback").json[0]["popId"] == pop


def test_send_pop_without_access(app, client):
    login_basic(client)
    pop = make_pop(app)  # published, but this user has no department access
    r = send(client, popId=pop)
    assert r.status_code == 404 and r.json == {"error": "POP not found or not available."}


@pytest.mark.parametrize("pop_id", ["3", 1.5, True])
def test_send_bad_pop_id(client, pop_id):
    login_basic(client)
    r = send(client, popId=pop_id)
    assert r.status_code == 400 and r.json == {"error": "POP id must be a whole number."}


@pytest.mark.parametrize("body", [{"description": "  "}, {}])
def test_send_blank_description(client, body):
    login_basic(client)
    r = client.post("/feedback", json=body)
    assert r.status_code == 400 and r.json == {"error": "Description is required."}


def test_list_scoped_to_user_and_admin_sees_all(app, client):
    login_basic(client)
    send(client, "from ana")
    login_basic(client, email="bob@test.com", name="Bob")  # id 2
    send(client, "from bob")
    assert [i["description"] for i in client.get("/feedback").json] == ["from bob"]

    login_basic(client)
    assert [i["description"] for i in client.get("/feedback").json] == ["from ana"]

    set_user(app, "ana@test.com", user_role="admin")
    login(client)
    items = client.get("/feedback").json
    assert [i["description"] for i in items] == ["from bob", "from ana"]  # newest first
    assert [i["userId"] for i in items] == [2, 1]


def test_answer_forbidden_for_basic(client):
    login_basic(client)
    send(client)
    r = client.post("/feedback/1/answer", json={"answer": "x"})
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}


def test_answer_flow(app, client):
    login_basic(client)
    send(client)
    login_admin(app, client)
    r = client.post("/feedback/1/answer", json={"answer": "  Fixed  "})
    assert r.status_code == 200 and r.json == {"message": "Feedback answered."}
    item = client.get("/feedback").json[0]
    assert item["status"] == "answered" and item["answer"] == "Fixed"
    assert item["answeredBy"] == 1 and item["answeredAtUtc"] is not None


def test_answer_validation_and_not_found(app, client):
    login_basic(client)
    send(client)
    login_admin(app, client)
    r = client.post("/feedback/1/answer", json={"answer": "   "})
    assert r.status_code == 400 and r.json == {"error": "Answer is required."}
    r = client.post("/feedback/999/answer", json={"answer": "   "})  # validation comes first
    assert r.status_code == 400 and r.json == {"error": "Answer is required."}
    r = client.post("/feedback/999/answer", json={"answer": "x"})
    assert r.status_code == 404 and r.json == {"error": "Feedback not found."}


def test_close_forbidden_for_basic(client):
    login_basic(client)
    send(client)
    r = client.post("/feedback/1/close")
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}


def test_close_flow(app, client):
    login_basic(client)
    send(client)
    login_admin(app, client)
    r = client.post("/feedback/1/close")
    assert r.status_code == 200 and r.json == {"message": "Feedback closed."}
    assert client.get("/feedback").json[0]["status"] == "closed"

    r = client.post("/feedback/1/close")
    assert r.status_code == 409 and r.json == {"error": "This feedback is already closed."}

    r = client.post("/feedback/1/answer", json={"answer": "late"})
    assert r.status_code == 409 and r.json == {"error": "This feedback is closed."}

    r = client.post("/feedback/999/close")
    assert r.status_code == 404 and r.json == {"error": "Feedback not found."}


def test_stale_admin_cookie_answer_is_forbidden(app, client):
    login_basic(client)
    send(client)
    set_user(app, "ana@test.com", user_role="admin")
    login(client)
    set_user(app, "ana@test.com", user_role="basic")
    r = client.post("/feedback/1/answer", json={"answer": "x"})
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}
