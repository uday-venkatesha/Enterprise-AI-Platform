from pydantic import BaseModel


# The shape of the /auth/login response. "bearer" is the standard token type
# for "send this in the Authorization header as: Bearer <token>".
class Token(BaseModel):
    access_token: str
    token_type: str