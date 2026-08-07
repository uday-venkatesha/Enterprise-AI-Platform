import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
import uuid
from collections.abc import Sequence

from sqlalchemy import select

async def create_document(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    uploaded_by: uuid.UUID,
    filename: str,
    content_type: str,
    size_bytes: int,
    object_key: str,
) -> Document:
    # This runs AFTER the bytes are safely in MinIO. It records the metadata row
    # that points at them. (The * forces keyword arguments, so callers must
    # write filename=..., size_bytes=... — harder to mix up the order.)
    document = Document(
        organization_id=organization_id,
        uploaded_by=uploaded_by,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        object_key=object_key,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document

async def list_documents_in_org(
    db: AsyncSession, organization_id: uuid.UUID
) -> Sequence[Document]:
    # Same isolation pattern as list_users_in_org: the WHERE clause guarantees
    # we only ever return THIS org's documents. Newest first so the most recent
    # upload shows at the top — handy when you're watching a status change.
    result = await db.execute(
        select(Document)
        .where(Document.organization_id == organization_id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


async def get_document_for_org(
    db: AsyncSession, document_id: uuid.UUID, organization_id: uuid.UUID
) -> Document | None:
    # THE SECURITY-CRITICAL PART: we filter by BOTH the document id AND the org.
    # We do NOT just db.get(Document, document_id) — that would fetch ANY org's
    # document. By requiring organization_id to match too, a user asking for a
    # document that isn't theirs gets None (which the route turns into a 404),
    # exactly as if it didn't exist. They can't even tell it's real.
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.organization_id == organization_id,
        )
    )
    return result.scalar_one_or_none()