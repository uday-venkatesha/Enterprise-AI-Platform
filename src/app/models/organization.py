import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Organization(Base):
    # The actual table name in Postgres.
    __tablename__ = "organizations"

    # UUID primary key instead of an auto-incrementing integer. In a
    # multi-tenant system, non-sequential IDs mean one tenant can't guess
    # another tenant's IDs by counting — a small but real security nicety.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # server_default=func.now() means Postgres itself stamps the creation time
    # (the DEFAULT now() in SQL), so it's correct no matter who inserts the row.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )