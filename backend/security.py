import base64
import binascii
import hashlib
import hmac
import os

ITERATIONS = 600_000
SALT_SIZE = 16
HASH_SIZE = 32


def hash_password(password):
    """Hash a password as "iterations.saltBase64.hashBase64" (same format as PasswordHasher.cs)."""
    salt = os.urandom(SALT_SIZE)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, HASH_SIZE)
    return f"{ITERATIONS}.{base64.b64encode(salt).decode()}.{base64.b64encode(digest).decode()}"


def verify_password(password, stored):
    """Check a password against a stored hash in constant time; False if the hash is malformed."""
    try:
        iterations, salt, expected = stored.split(".")
        salt = base64.b64decode(salt, validate=True)
        expected = base64.b64decode(expected, validate=True)
        iterations = int(iterations)
    except (AttributeError, ValueError, binascii.Error):
        return False
    if iterations < 1 or not expected:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, len(expected))
    return hmac.compare_digest(actual, expected)
