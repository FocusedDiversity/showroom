"""add_palette_and_layout_slugs_to_authoring_sessions

Revision ID: c8a2d3e5f7b1
Revises: b3f1a8c2d4e5
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8a2d3e5f7b1'
down_revision: Union[str, Sequence[str], None] = 'b3f1a8c2d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE authoring_sessions ADD COLUMN palette_slug TEXT NOT NULL DEFAULT 'arctic-breeze'")
    op.execute("ALTER TABLE authoring_sessions ADD COLUMN layout_slug TEXT NOT NULL DEFAULT 'editorial'")


def downgrade() -> None:
    op.execute("ALTER TABLE authoring_sessions DROP COLUMN IF EXISTS layout_slug")
    op.execute("ALTER TABLE authoring_sessions DROP COLUMN IF EXISTS palette_slug")
