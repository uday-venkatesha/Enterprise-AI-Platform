"""add hnsw index on chunk embeddings

Revision ID: 74e213ae1e67
Revises: ec3343b1ea2d
Create Date: 2026-08-17 23:01:14.018841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74e213ae1e67'
down_revision: Union[str, Sequence[str], None] = 'ec3343b1ea2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Build an HNSW index on the embedding column, using the cosine-distance
    # operator class (vector_cosine_ops). This is what makes nearest-neighbor
    # search fast. Our search query MUST use the matching cosine operator (<=>)
    # for this index to kick in.
    op.execute(
        "CREATE INDEX chunks_embedding_hnsw_idx "
        "ON chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS chunks_embedding_hnsw_idx")