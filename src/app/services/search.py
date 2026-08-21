import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
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
async def keyword_search_chunks(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    query: str,
    limit: int = 20,
) -> Sequence[Chunk]:
    # Build the same to_tsvector expression the index uses, so the index applies.
    tsv = func.to_tsvector("english", Chunk.content)
    # plainto_tsquery turns a plain phrase into a query safely (handles multiple
    # words as AND, ignores punctuation) — no need to sanitize user input.
    tsq = func.plainto_tsquery("english", query)

    result = await db.execute(
        select(Chunk)
        .where(Chunk.organization_id == organization_id)   # tenant isolation, same as always
        .where(tsv.op("@@")(tsq))                          # keep only chunks that MATCH the words
        .order_by(func.ts_rank(tsv, tsq).desc())           # best keyword matches first
        .limit(limit)
    )
    return result.scalars().all()


def reciprocal_rank_fusion(
    result_lists: list[Sequence[Chunk]],
    *,
    k: int = 60,
    limit: int = 5,
) -> list[Chunk]:
    # scores: chunk_id -> combined RRF score. chunk_by_id: remember the objects.
    scores: dict = {}
    chunk_by_id: dict = {}

    # For EACH list (semantic, keyword), walk it in rank order and add points.
    for results in result_lists:
        for rank, chunk in enumerate(results, start=1):
            # THE RRF FORMULA: a chunk's contribution depends only on its POSITION,
            # not its raw score — which is how we sidestep the different-scales problem.
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank)
            chunk_by_id[chunk.id] = chunk

    # Sort all seen chunks by total score (highest first), take the top `limit`.
    ranked_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)
    return [chunk_by_id[cid] for cid in ranked_ids[:limit]]


async def hybrid_search_chunks(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    query: str,
    query_embedding: list[float],
    limit: int = 5,
    candidate_pool: int = 20,
) -> list[Chunk]:
    # Pull a POOL of candidates from each method (more than we'll finally return),
    # so fusion has enough to work with.
    semantic_results = await search_chunks(          # your existing semantic search
        db, organization_id=organization_id,
        query_embedding=query_embedding, limit=candidate_pool,
    )
    keyword_results = await keyword_search_chunks(   # the new keyword search
        db, organization_id=organization_id,
        query=query, limit=candidate_pool,
    )
    # Fuse the two ranked lists into one, keep the best `limit`.
    return reciprocal_rank_fusion([semantic_results, keyword_results], limit=limit)
def deduplicate_chunks(chunks: list[Chunk]) -> list[Chunk]:
    # Drop chunks whose text we've already seen, keeping the FIRST occurrence
    # (which is the higher-ranked one). Guards against the same content appearing
    # twice — e.g. from a document uploaded more than once.
    seen: set[str] = set()
    unique: list[Chunk] = []
    for chunk in chunks:
        # Normalize lightly so trivial whitespace differences still count as dupes.
        key = chunk.content.strip()
        if key not in seen:
            seen.add(key)
            unique.append(chunk)
    return unique