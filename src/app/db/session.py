from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# The engine is the actual connection pool to Postgres — created ONCE for the
# whole app. echo=settings.debug logs every SQL statement while debugging,
# which is genuinely useful for learning (you see the SQL the ORM generates).
engine = create_async_engine(settings.database_url, echo=settings.debug)

# A factory that produces new database sessions. A "session" is one unit of
# work — you open it, do some queries/writes, commit, close. expire_on_commit
# =False keeps objects usable after commit (avoids surprise extra queries).
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# This is a FastAPI DEPENDENCY. Any route that declares `db = Depends(get_db)`
# gets a fresh session, and the `async with` block guarantees the session is
# properly closed when the request finishes — even if the route raises. This
# one function is how every future route will talk to the database.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session