import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# The four roles from the project brief. Inheriting from `str` too means each
# member IS its string value ("admin"), which makes it painless to store,
# serialize to JSON, and compare later in the RBAC step.
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # The foreign key that makes this multi-tenant: every user is tied to one
    # organization. ondelete="CASCADE" means deleting an org deletes its users.
    # index=True because we'll constantly filter "users WHERE organization_id = ..."
    # and an index makes that fast.
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # unique + index: no two accounts share an email, and lookups by email
    # (which every login does) are fast.
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # We NEVER store the raw password — only a one-way hash of it (step 2b).
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # The role column uses our enum. New users default to the least-privileged
    # role; you have to deliberately promote someone.
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole), nullable=False, default=UserRole.EMPLOYEE
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )