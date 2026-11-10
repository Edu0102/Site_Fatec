import base64

import pytest

from security import hash_password, verify_password

# Made by PasswordHasher.cs for agatinho@test.com (password "mypassword123")
CSHARP_HASH = "600000.GVWNQ53JXqJrOvdWLNTc6Q==.50BJhQqB+D9Zqs+LP4hAiHEV+cc7uNQTQDYHpCgLcw8="


def test_verifies_hash_made_by_csharp():
    assert verify_password("mypassword123", CSHARP_HASH)
    assert not verify_password("mypassword124", CSHARP_HASH)


def test_format_and_roundtrip():
    h = hash_password("secret123")
    it, salt, digest = h.split(".")
    assert it == "600000" and len(base64.b64decode(salt)) == 16 and len(base64.b64decode(digest)) == 32
    assert verify_password("secret123", h) and not verify_password("Secret123", h)
    assert hash_password("secret123") != h  # random salt


@pytest.mark.parametrize("bad", ["", "abc", "x.y.z", "600000.!!!.???", None])
def test_malformed_hash_is_false(bad):
    assert verify_password("whatever1", bad) is False
