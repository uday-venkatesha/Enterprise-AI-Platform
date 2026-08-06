import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


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