import bcrypt
from datetime import datetime, timedelta, timezone
import jwt
from app.config import settings


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

def create_access_token(subject: str) -> str:
    # "subject" is WHO the token is about — we'll pass the user's id as a string.
    # Compute the absolute expiry time from now.
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    # These are the "claims" that go inside the token. "sub" and "exp" are
    # standard claim names PyJWT understands ("exp" is auto-checked on decode).
    to_encode = {"sub": subject, "exp": expire}
    # Sign the claims with our secret. The output is the JWT string.
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)