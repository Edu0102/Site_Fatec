import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    # Fresh app with its own temporary database for each test
    return create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    # HTTP test client that keeps cookies between requests
    return app.test_client()
