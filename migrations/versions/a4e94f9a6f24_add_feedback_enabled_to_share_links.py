"""add_feedback_enabled_to_share_links

Revision ID: a4e94f9a6f24
Revises: dec772b583f9
Create Date: 2026-04-01 05:21:38.587257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4e94f9a6f24'
down_revision: Union[str, Sequence[str], None] = 'dec772b583f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE share_links ADD COLUMN feedback_enabled BOOLEAN DEFAULT TRUE")


def downgrade() -> None:
    op.execute("ALTER TABLE share_links DROP COLUMN IF EXISTS feedback_enabled")
