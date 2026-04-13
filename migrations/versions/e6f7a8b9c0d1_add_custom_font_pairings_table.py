"""add_custom_font_pairings_table

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE custom_font_pairings (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            font_data JSONB NOT NULL,
            source TEXT NOT NULL DEFAULT 'manual',
            source_filename TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        ALTER TABLE authoring_sessions ADD COLUMN font_slug TEXT NOT NULL DEFAULT 'classic-serif';
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE authoring_sessions DROP COLUMN IF EXISTS font_slug;
        DROP TABLE IF EXISTS custom_font_pairings;
    """)
