import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.users import UserRole

# What the client sends to create a user
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    organization_id: uuid.UUID
    role: UserRole = UserRole.EMPLOYEE

# What is returned in the API response (hiding the hashed_password)
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    email: EmailStr
    role: UserRole
    created_at: datetime