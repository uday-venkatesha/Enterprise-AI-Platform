from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    # LIVENESS: "is the process running?" No dependencies, always fast.
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    # READINESS: "can I actually do useful work?" We prove it by running the
    # simplest possible query. If the database is unreachable, this raises and
    # returns an error — which is exactly what a load balancer needs to know.
    await db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}