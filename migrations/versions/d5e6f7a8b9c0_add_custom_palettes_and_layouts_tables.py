"""add_custom_palettes_and_layouts_tables

Revision ID: d5e6f7a8b9c0
Revises: c8a2d3e5f7b1
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c8a2d3e5f7b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE custom_palettes (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            palette_data JSONB NOT NULL,
            source TEXT NOT NULL DEFAULT 'pptx',
            source_filename TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE custom_layouts (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL DEFAULT '',
            layout_data JSONB NOT NULL,
            base_layout_slug TEXT NOT NULL DEFAULT 'editorial',
            source TEXT NOT NULL DEFAULT 'pptx',
            source_filename TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS custom_layouts;
        DROP TABLE IF EXISTS custom_palettes;
    """)
