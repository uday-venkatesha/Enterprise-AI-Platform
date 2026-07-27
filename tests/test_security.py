from app.core.security import hash_password, verify_password


def test_hashing_is_not_plaintext():
    # The stored hash must never equal the raw password.
    hashed = hash_password("supersecret123")
    assert hashed != "supersecret123"
    # And every bcrypt hash starts with this prefix.
    assert hashed.startswith("$2b$")


def test_verify_password_roundtrip():
    hashed = hash_password("supersecret123")
    assert verify_password("supersecret123", hashed) is True   # correct password
    assert verify_password("wrongpassword", hashed) is False   # wrong password