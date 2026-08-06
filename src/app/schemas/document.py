import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# What we return after upload / when listing. The client gets metadata and the
# id, but never the raw bytes — those are fetched separately when needed.
class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    organization_id: uuid.UUID
    created_at: datetime