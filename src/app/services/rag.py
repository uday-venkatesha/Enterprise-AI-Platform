import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.embeddings import embed_texts
from app.core.llm import generate_answer
from app.models.chunk import Chunk
from app.services.search import hybrid_search_chunks
from app.core.llm import generate_answer, rerank_chunks       # add rerank_chunks
from app.services.search import hybrid_search_chunks, deduplicate_chunks

async def answer_question(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    question: str,
    limit: int = 5,
) -> tuple[str, list[Chunk]]:
    # 1) RETRIEVE — the exact Phase 5 pipeline: embed the question, find the
    # nearest chunks in this org. We're reusing search_chunks, not rewriting it.
    query_embedding = embed_texts([question])[0]
    chunks = list(await hybrid_search_chunks(
        db,
        organization_id=organization_id,
        query=question,                  # NEW: keyword side needs the raw text
        query_embedding=query_embedding, # semantic side needs the vector
        limit=limit,
    ))

    # 2) If retrieval found nothing (e.g. the org has no documents), don't even
    # call the LLM — just say we don't know. Saves an API call and can't hallucinate.
    if not chunks:
        return "I don't know based on the available documents.", []

    # 3) GENERATE — hand the chunks + question to the LLM under strict rules.
    answer = generate_answer(question, chunks)

    # Return BOTH the answer text and the chunks it was based on, so the endpoint
    # can present citations.
    return answer, chunks

async def answer_question(db, *, organization_id, question, limit=5):
    query_embedding = embed_texts([question])[0]

    # STAGE 1: retrieve a WIDE pool of candidates (20, not 5).
    candidates = list(await hybrid_search_chunks(
        db,
        organization_id=organization_id,
        query=question,
        query_embedding=query_embedding,
        limit=20,                     # cast a wide net
    ))

    # Remove duplicate content before spending reranking effort on it.
    candidates = deduplicate_chunks(candidates)

    if not candidates:
        return "I don't know based on the available documents.", []

    # STAGE 2: rerank the pool with the LLM and keep the best `limit`.
    chunks = rerank_chunks(question, candidates, top_n=limit)

    # Generate the grounded answer from the reranked top chunks.
    answer = generate_answer(question, chunks)
    return answer, chunks