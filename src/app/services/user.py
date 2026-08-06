import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User
from app.schemas.user import UserCreate
from app.core.security import hash_password
from collections.abc import Sequence


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    # db.get is the clean way to fetch a row by its primary key.
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed = hash_password(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed,
        organization_id=user_in.organization_id,
        role=user_in.role,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def list_users_in_org(
    db: AsyncSession, organization_id: uuid.UUID
) -> Sequence[User]:
    # The isolation happens HERE, in the WHERE clause. This query can only ever
    # return users whose organization_id matches the one we pass in. There is
    # no code path that returns another org's users, because the filter isn't
    # optional — it's baked into the only function that lists users.
    result = await db.execute(
        select(User).where(User.organization_id == organization_id)
    )
    # .scalars().all() unwraps the rows into a list of User objects.
    return result.scalars().all()