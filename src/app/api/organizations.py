from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.organization import OrganizationCreate, OrganizationRead
from app.services import organization as organization_service

router = APIRouter(prefix="/organizations", tags=["organizations"])


# response_model=OrganizationRead means FastAPI validates & filters the return
# value through that schema before sending it. status_code=201 is the correct
# HTTP code for "created a new resource."
@router.post("", response_model=OrganizationRead, status_code=201)
async def create_organization(
    org_in: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
):
    return await organization_service.create_organization(db, org_in)