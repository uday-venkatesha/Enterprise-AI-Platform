import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
import enum 
from sqlalchemy import Enum as SAEnum   

# The lifecycle a document moves through. Explicit states beat a loose string —
# you can only ever be in one of these, and typos become impossible.
class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"       # bytes stored, not yet processed
    PROCESSING = "processing"   # worker is actively reading it
    PROCESSED = "processed"     # text successfully extracted
    FAILED = "failed"           # something went wrong during processing


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Same tenant-isolation pattern as users: every document belongs to one org,
    # indexed because we'll always filter documents by organization_id.
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Who uploaded it — useful for audit and per-user views later.
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # The original name the user's file had, for display.
    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # The file's MIME type, e.g. "application/pdf". We record what was uploaded.
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)

    # Size in bytes. BigInteger because files can exceed a normal int's range.
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # THE POINTER: where the bytes live in MinIO. The DB row and the blob are
    # linked by this key. Given this, we can always fetch the file back.
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # NEW: where this document is in its lifecycle. New uploads start UPLOADED.
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADED, server_default=DocumentStatus.UPLOADED.value
    )

    # NEW: when processing finishes we'll store the extracted text here. Nullable
    # because it's empty until the worker fills it. Text = a large text column.
    extracted_text: Mapped[str | None] = mapped_column(nullable=True)
