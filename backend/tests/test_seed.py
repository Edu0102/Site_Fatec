from db import get_db
from repositories import pops
from seed import create_admin, seed_test_data
from tests.conftest import login


def test_seed_logins_and_visibility(app, client):
    seed_test_data(app)
    seed_test_data(app)  # running it twice must not duplicate anything
    with app.app_context():
        db = get_db()
        assert db.execute('SELECT COUNT(*) FROM "User"').fetchone()[0] == 3
        assert db.execute('SELECT COUNT(*) FROM "Pop"').fetchone()[0] == 1
        basic_id = db.execute('SELECT user_id FROM "User" WHERE user_email = ?', ("basic@test.com",)).fetchone()[0]
        assert pops.get_visible(1, basic_id, "basic") is not None
    assert login(client, "admin@test.com").status_code == 200
    assert client.get("/api/auth/me").json["role"] == "admin"
    assert login(client, "basic@test.com").status_code == 200
    assert login(client, "inactive@test.com").status_code == 401


def test_create_admin(app, client):
    assert create_admin(app, "boss@site.com", "Boss", "a-long-password") is True
    assert create_admin(app, "boss@site.com", "Boss", "a-long-password") is False  # already exists
    assert login(client, "boss@site.com", "a-long-password").status_code == 200
    assert client.get("/api/auth/me").json["role"] == "admin"
