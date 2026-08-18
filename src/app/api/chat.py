import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_organization_id
from app.db.session import get_db
from app.schemas.chat import ChatAnswer, SourceCitation
from app.services import rag as rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    limit: int = 5


@router.post("", response_model=ChatAnswer)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_current_organization_id),  # auth + org scope, as always
):
    # Retrieve + generate.
    answer, chunks = await rag_service.answer_question(
        db,
        organization_id=org_id,
        question=body.question,
        limit=body.limit,
    )

    # Turn the chunks into numbered citations — the SAME numbering (start=1) the
    # LLM saw in build_context, so [1] in the answer text lines up with sources[0].
    sources = [
        SourceCitation(
            citation=index,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
        )
        for index, chunk in enumerate(chunks, start=1)
    ]

    return ChatAnswer(answer=answer, sources=sources)