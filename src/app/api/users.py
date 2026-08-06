from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.users import User,UserRole
from app.schemas.user import UserCreate, UserRead
from app.services import user as user_service
from app.api.deps import get_current_user, require_role

import uuid
from app.api.deps import get_current_organization_id 

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    # The guard. FastAPI runs require_role(...)'s checker before the body
    # executes, so a non-admin gets a 403 and never reaches the creation logic.
    # The leading underscore signals "here for its side effect, not used below."
    _admin: User = Depends(require_role(UserRole.ADMIN)),
):
    existing = await user_service.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # create_user returns a User that DOES contain hashed_password — but
    # response_model=UserRead strips it out before it ever leaves the app.
    return await user_service.create_user(db, user_in)


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)):
    # If we reach this line, the request was authenticated, and current_user
    # IS the logged-in user.
    return current_user


@router.get("", response_model=list[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    # This one dependency does everything: forces authentication AND yields the
    # caller's org id. No org id in the signature that a client could override.
    org_id: uuid.UUID = Depends(get_current_organization_id),
):
    # response_model=list[UserRead] filters EACH row through UserRead, so no
    # hashes leak even in a bulk listing.
    return await user_service.list_users_in_org(db, org_id)