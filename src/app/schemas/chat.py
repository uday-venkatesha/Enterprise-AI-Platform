import uuid

from pydantic import BaseModel, ConfigDict


# One cited source. `citation` is the [n] number that appears in the answer text;
# the rest tells the user WHAT [n] actually is (which document, which chunk).
class SourceCitation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    citation: int
    document_id: uuid.UUID
    chunk_index: int
    content: str


# The full response: the written answer, plus the list of sources behind it.
class ChatAnswer(BaseModel):
    answer: str
    sources: list[SourceCitation]