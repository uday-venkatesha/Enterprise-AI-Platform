import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User, UserRole  # UserRole is new to this import


from app.config import settings
from app.db.session import get_db
from app.services import user as user_service

# This declares "protected routes expect a Bearer token." tokenUrl tells the
# /docs page WHERE to get a token (our login route), so the Swagger "Authorize"
# button works. It does NOT change routing — it's metadata + header extraction.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),          # pulls the token out of the header
    db: AsyncSession = Depends(get_db),
) -> User:
    # One reusable error for every failure path. We stay vague on purpose —
    # never tell an attacker WHICH part failed.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Verify the signature AND the expiry in one call. If the token was
        # tampered with or has expired, this raises.
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = payload.get("sub")            # the user id we stored at login
        if user_id is None:
            raise credentials_exception
        user_uuid = uuid.UUID(user_id)          # turn the string back into a UUID
    except (jwt.PyJWTError, ValueError):
        # jwt.PyJWTError = bad/expired token; ValueError = malformed uuid.
        raise credentials_exception

    # The token was valid — but confirm the user still exists (they might have
    # been deleted after the token was issued).
    user = await user_service.get_user_by_id(db, user_uuid)
    if user is None:
        raise credentials_exception
    return user


# This is a DEPENDENCY FACTORY: a function that BUILDS and returns a dependency.
# We call require_role(UserRole.ADMIN) and it hands back a checker function
# tailored to those roles. This is why we can reuse one piece of code for
# "admin only", "hr or manager", etc.
def require_role(*allowed_roles: UserRole):
    # The inner function is the actual dependency FastAPI will run per request.
    # It depends on get_current_user, so authentication happens FIRST (you must
    # be logged in), and only then do we check the role.
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            # 403 Forbidden is the correct code here — distinct from 401.
            # 401 = "I don't know who you are." 403 = "I know exactly who you
            # are, and you're not allowed." Getting this distinction right
            # matters both for correctness and for clear API behavior.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        # Passed the check — hand the user object through so the route can use it.
        return current_user

    return role_checker

# Depends on get_current_user, then extracts just the org id. Any route that
# declares `org_id: uuid.UUID = Depends(get_current_organization_id)` receives
# the authenticated caller's organization and literally cannot see another's,
# because this value comes from their OWN token-derived identity — not from
# anything the client sends in the request.
def get_current_organization_id(
    current_user: User = Depends(get_current_user),
) -> uuid.UUID:
    return current_user.organization_id