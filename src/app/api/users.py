from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services import user as user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    # Reject duplicate emails with a clear 400 instead of a raw database error.
    existing = await user_service.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    # create_user returns a User object that DOES contain hashed_password —
    # but response_model=UserRead strips it out before it ever leaves the app.
    return await user_service.create_user(db, user_in)
