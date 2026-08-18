import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk


async def search_chunks(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    query_embedding: list[float],
    limit: int = 5,
) -> Sequence[Chunk]:
    # Chunk.embedding.cosine_distance(query_embedding) is pgvector's SQLAlchemy
    # helper for the cosine-distance operator (<=>). SMALLER distance = MORE
    # similar in meaning. So ordering ascending by distance puts the most
    # relevant chunks first.
    distance = Chunk.embedding.cosine_distance(query_embedding)

    result = await db.execute(
        select(Chunk)
        # TENANT ISOLATION, unchanged: only ever search THIS org's chunks. This
        # is why we denormalized organization_id onto chunks back in 4c — we can
        # filter here directly, no join, and the vector index still applies.
        .where(Chunk.organization_id == organization_id)
        # Order by nearness and take the top `limit`. pgvector uses the HNSW
        # index to do this without scanning every row.
        .order_by(distance)
        .limit(limit)
    )
    return result.scalars().all()