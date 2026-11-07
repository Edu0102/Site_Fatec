import pytest

from app import create_app
from db import get_db


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200 and r.get_data(as_text=True) == "Server is running"


def test_schema_created(app):
    with app.app_context():
        names = {r[0] for r in get_db().execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"User", "Department", "UserDepartment", "Pop", "Link", "PhoneNumber",
            "PopLink", "PopPhone", "PopDepartment"} <= names


def test_missing_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"DATABASE": ":memory:"})
