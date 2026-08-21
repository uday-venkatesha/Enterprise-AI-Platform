"""add full text search index on chunks

Revision ID: 75414908d885
Revises: 74e213ae1e67
Create Date: 2026-08-19 23:07:59.600002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75414908d885'
down_revision: Union[str, Sequence[str], None] = '74e213ae1e67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
   # A GIN index on the "searchable words" form of each chunk's content.
    # to_tsvector('english', content) turns text into stemmed, stop-word-free
    # tokens; GIN is the index type built for that. This makes keyword search fast.
    op.execute(
        "CREATE INDEX chunks_content_fts_idx ON chunks "
        "USING GIN (to_tsvector('english', content))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS chunks_content_fts_idx")
