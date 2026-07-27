from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate


async def create_organization(db: AsyncSession, org_in: OrganizationCreate) -> Organization:
    # Build the ORM object from the validated input schema.
    org = Organization(name=org_in.name)
    db.add(org)              # stage it in the session
    await db.commit()        # write to Postgres
    await db.refresh(org)    # reload so server-generated fields (id, created_at) are populated
    return org