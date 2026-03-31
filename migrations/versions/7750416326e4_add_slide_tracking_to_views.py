"""add_slide_tracking_to_views

Revision ID: 7750416326e4
Revises: 
Create Date: 2026-03-31 09:23:58.563803

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7750416326e4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('views', sa.Column('current_slide', sa.Integer(), nullable=True))
    op.add_column('views', sa.Column('total_slides', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('views', 'total_slides')
    op.drop_column('views', 'current_slide')
