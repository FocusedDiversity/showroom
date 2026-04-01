"""add_slide_feedback_table

Revision ID: dec772b583f9
Revises: 7750416326e4
Create Date: 2026-03-31 16:12:35.676040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dec772b583f9'
down_revision: Union[str, Sequence[str], None] = '7750416326e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE slide_feedback (
            id SERIAL PRIMARY KEY,
            view_id INTEGER NOT NULL,
            slide_number INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (view_id) REFERENCES views(id) ON DELETE CASCADE
        );
        CREATE INDEX idx_slide_feedback_view_id ON slide_feedback(view_id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS slide_feedback;")
