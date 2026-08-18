import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_organization_id
from app.core.embeddings import embed_texts
from app.db.session import get_db
from app.schemas.search import SearchResult
from app.services import search as search_service

router = APIRouter(prefix="/search", tags=["search"])


# The request body: just the user's question and how many results they want.
class SearchQuery(BaseModel):
    query: str
    limit: int = 5


@router.post("", response_model=list[SearchResult])
async def search(
    body: SearchQuery,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_organization_id),  # auth + org, same as always
):
    # 1) Embed the QUESTION with the SAME model used for the chunks. This is
    # essential — you can only compare vectors from the same embedding model.
    # embed_texts takes a list and returns a list, so we pass [query] and take [0].
    query_embedding = embed_texts([body.query])[0]

    # 2) Ask pgvector for the nearest chunks within this org.
    chunks = await search_service.search_chunks(
        db,
        organization_id=org_id,
        query_embedding=query_embedding,
        limit=body.limit,
    )
    return chunks