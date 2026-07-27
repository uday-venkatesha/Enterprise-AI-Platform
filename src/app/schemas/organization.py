import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# What the client SENDS to create an org. Just a name.
class OrganizationCreate(BaseModel):
    name: str


# What we SEND BACK. from_attributes=True lets Pydantic build this straight
# from a SQLAlchemy ORM object (reading org.id, org.name, etc.) instead of
# requiring a plain dict.
class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime