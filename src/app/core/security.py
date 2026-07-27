import bcrypt


def hash_password(password: str) -> str:
    # bcrypt works on bytes, not str, so encode first.
    pwd_bytes = password.encode("utf-8")
    # gensalt() produces a fresh random salt every call — this is why the same
    # password hashes differently for two different users.
    salt = bcrypt.gensalt()
    # hashpw combines password + salt into the final hash. The salt is embedded
    # INSIDE the returned value, so we don't store it separately.
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    # Store it as a str (it goes into a String column). A bcrypt hash always
    # begins with "$2b$" — you'll see that in the database shortly.
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # checkpw re-hashes plain_password using the salt embedded in the stored
    # hash, then compares. Returns True only on a match. This is what login uses.
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )