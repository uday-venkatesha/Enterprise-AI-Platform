import logging
from contextlib import asynccontextmanager
from app.api import health, organizations, users

from fastapi import FastAPI

from app.config import settings
from app.api import health

# Configure logging once, at the top level. Everywhere else we just call
# logging.getLogger(__name__) and messages flow through this config.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


# "lifespan" runs code once at startup (before "yield") and once at shutdown
# (after "yield"). Right now it just logs; later this is where we'll open and
# close database connections, warm caches, etc. Doing it here (not at import)
# means resources are tied to the app's actual run, which matters for tests.
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (env=%s)", settings.app_name, settings.environment)
    yield
    logger.info("Shutting down %s", settings.app_name)


# The application object. Uvicorn looks for this variable ("app") to run it.
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# Attach the health router. Every new feature area later = another router
# and another include_router line here.
app.include_router(health.router)
app.include_router(organizations.router)
app.include_router(users.router)