from db import get_db
from repositories import pops
from tests.conftest import give_access, make_pop, register


def test_new_tables_exist(app):
    with app.app_context():
        cols = lambda t: {r[1] for r in get_db().execute(f'PRAGMA table_info("{t}")')}
        assert cols("Feedback") == {"feedback_id", "user_id", "pop_id", "answered_by", "feedback_description",
                                    "feedback_status", "feedback_answer", "created_at_utc", "answered_at_utc"}
        assert cols("Checklist") == {"checklist_id", "pop_id", "user_id", "checklist_description",
                                     "created_at_utc", "completed_at_utc"}
        assert cols("StandardCheck") == {"standard_check_id", "pop_id", "check_text", "check_order"}
        assert cols("ChecklistItemResult") == {"checklist_item_result_id", "checklist_id", "standard_check_id", "is_checked"}


def test_feedback_status_default_and_check(app, client):
    import sqlite3
    import pytest
    register(client)
    with app.app_context():
        db = get_db()
        db.execute('INSERT INTO "Feedback" (user_id, feedback_description) VALUES (1, ?)', ("hi",))
        assert db.execute('SELECT feedback_status FROM "Feedback"').fetchone()[0] == "open"
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('INSERT INTO "Feedback" (user_id, feedback_description, feedback_status) VALUES (1, ?, ?)', ("x", "weird"))


def test_item_result_unique(app, client):
    import sqlite3
    import pytest
    register(client)
    pop = make_pop(app)
    with app.app_context():
        db = get_db()
        check = db.execute('INSERT INTO "StandardCheck" (pop_id, check_text, check_order) VALUES (?, ?, 1)', (pop, "a")).lastrowid
        cl = db.execute('INSERT INTO "Checklist" (pop_id, user_id) VALUES (?, 1)', (pop,)).lastrowid
        db.execute('INSERT INTO "ChecklistItemResult" (checklist_id, standard_check_id) VALUES (?, ?)', (cl, check))
        assert db.execute('SELECT is_checked FROM "ChecklistItemResult"').fetchone()[0] == 0
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('INSERT INTO "ChecklistItemResult" (checklist_id, standard_check_id) VALUES (?, ?)', (cl, check))


def test_pop_visibility(app, client):
    register(client)                          # user 1
    register(client, email="b@test.com")      # user 2
    pub, draft, other = make_pop(app), make_pop(app, status="draft"), make_pop(app)
    give_access(app, 2, pub)
    give_access(app, 2, draft)
    with app.app_context():
        assert pops.get_visible(pub, 2, "basic") is not None
        assert pops.get_visible(draft, 2, "basic") is None          # not published
        assert pops.get_visible(other, 2, "basic") is None          # no department access
        assert pops.get_visible(other, 2, "admin") is not None      # admins see everything
        assert pops.get_visible(draft, 1, "admin") is not None
        assert pops.get_visible(999, 1, "admin") is None


def test_pop_visibility_respects_access_window(app, client):
    register(client)
    p_revoked, p_future, p_expired = make_pop(app), make_pop(app), make_pop(app)
    give_access(app, 1, p_revoked, revoked="2020-01-01T00:00:00.000000Z")
    give_access(app, 1, p_future, valid_from="2999-01-01T00:00:00.000000Z")
    give_access(app, 1, p_expired, expires="2020-01-01T00:00:00.000000Z")
    with app.app_context():
        assert pops.get_visible(p_revoked, 1, "basic") is None
        assert pops.get_visible(p_future, 1, "basic") is None
        assert pops.get_visible(p_expired, 1, "basic") is None
