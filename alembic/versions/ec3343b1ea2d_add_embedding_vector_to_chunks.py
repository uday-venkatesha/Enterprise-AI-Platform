"""add embedding vector to chunks

Revision ID: ec3343b1ea2d
Revises: 88a15833b079
Create Date: 2026-08-13 13:17:55.202733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'ec3343b1ea2d'
down_revision: Union[str, Sequence[str], None] = '88a15833b079'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column('chunks', sa.Column('embedding', Vector(1536), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('chunks', 'embedding')
    op.execute("DROP EXTENSION IF EXISTS vector")
