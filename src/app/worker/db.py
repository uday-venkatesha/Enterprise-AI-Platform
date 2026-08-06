from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# The API uses an ASYNC engine. The worker uses a SYNC one, because Celery tasks
# are ordinary synchronous functions. We derive the sync URL from the async one
# by swapping the driver: asyncpg (async) -> psycopg (sync).
sync_database_url = settings.database_url.replace("+asyncpg", "+psycopg")

# echo=False here to keep worker logs readable.
sync_engine = create_engine(sync_database_url, echo=False)
SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)