import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from pgvector.sqlalchemy import Vector 


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # The document this chunk was cut from. CASCADE: delete the document and its
    # chunks vanish too. Indexed because we'll fetch "all chunks for document X".
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Carry the org id onto the chunk too. This looks redundant (we could join
    # through documents), but denormalizing it here means Phase 6's search can
    # filter chunks by org DIRECTLY — the tenant-isolation filter you know,
    # applied at the level we'll actually be searching. Indexed for that.
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # This chunk's position in the document (0, 1, 2, ...). Lets us reassemble
    # order and cite "chunk 3 of this doc" later.
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # The actual text of this chunk. Text = unbounded length.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
   

