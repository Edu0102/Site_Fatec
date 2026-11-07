import pytest

from tests.conftest import give_access, login_admin, login_basic, make_pop


def url(pop_id):
    return f"/pops/{pop_id}/standard-checks"


def test_unauthenticated(app, client):
    pop = make_pop(app)
    r = client.get(url(pop))
    assert r.status_code == 401 and r.json == {"error": "Not authenticated."}
    r = client.post(url(pop), json={"checkText": "x", "checkOrder": 1})
    assert r.status_code == 401 and r.json == {"error": "Not authenticated."}


def test_admin_creates_and_lists(app):
    admin = login_admin(app, app.test_client(), "ana@test.com")
    pop = make_pop(app)
    r1 = admin.post(url(pop), json={"checkText": "Second", "checkOrder": 2})
    r2 = admin.post(url(pop), json={"checkText": "First", "checkOrder": 1})
    assert r1.status_code == 200 and r1.json["message"] == "Standard check created."
    assert r2.status_code == 200
    r = admin.get(url(pop))
    assert r.status_code == 200
    assert r.json == [
        {"id": r2.json["id"], "popId": pop, "checkText": "First", "checkOrder": 1},
        {"id": r1.json["id"], "popId": pop, "checkText": "Second", "checkOrder": 2},
    ]


def test_basic_user_cannot_create(app):
    login_admin(app, app.test_client(), "ana@test.com")
    bob = login_basic(app.test_client(), "bob@test.com")
    pop = make_pop(app)
    r = bob.post(url(pop), json={"checkText": "x", "checkOrder": 1})
    assert r.status_code == 403 and r.json == {"error": "Forbidden."}


def test_admin_pop_not_found(app):
    admin = login_admin(app, app.test_client(), "ana@test.com")
    r = admin.post(url(999), json={"checkText": "x", "checkOrder": 1})
    assert r.status_code == 404 and r.json == {"error": "POP not found."}


@pytest.mark.parametrize("body, message", [
    ({}, "Check text is required."),
    ({"checkText": "   ", "checkOrder": 1}, "Check text is required."),
    ({"checkText": "x"}, "Check order must be a whole number."),
    ({"checkText": "x", "checkOrder": "1"}, "Check order must be a whole number."),
    ({"checkText": "x", "checkOrder": 1.5}, "Check order must be a whole number."),
    ({"checkText": "x", "checkOrder": True}, "Check order must be a whole number."),
])
def test_validation_runs_before_admin_check(app, body, message):
    login_admin(app, app.test_client(), "ana@test.com")
    bob = login_basic(app.test_client(), "bob@test.com")
    pop = make_pop(app)
    r = bob.post(url(pop), json=body)
    assert r.status_code == 400 and r.json == {"error": message}


def test_visibility(app):
    admin = login_admin(app, app.test_client(), "ana@test.com")
    bob = login_basic(app.test_client(), "bob@test.com")  # user id 2
    published = make_pop(app, title="Published")
    draft = make_pop(app, status="draft", title="Draft")
    admin.post(url(published), json={"checkText": "x", "checkOrder": 1})

    r = bob.get(url(published))
    assert r.status_code == 404 and r.json == {"error": "POP not found or not available."}

    give_access(app, 2, published)
    give_access(app, 2, draft)
    r = bob.get(url(published))
    assert r.status_code == 200 and [c["checkText"] for c in r.json] == ["x"]
    assert bob.get(url(draft)).status_code == 404

    r = admin.get(url(draft))
    assert r.status_code == 200 and r.json == []
