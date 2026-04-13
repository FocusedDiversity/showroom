"""add_authoring_tables

Revision ID: b3f1a8c2d4e5
Revises: dec772b583f9
Create Date: 2026-04-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f1a8c2d4e5'
down_revision: Union[str, Sequence[str], None] = 'a4e94f9a6f24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE collages (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            tags TEXT[],
            storage_path TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'upload',
            recraft_prompt TEXT,
            width INTEGER,
            height INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE authoring_sessions (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            markdown_content TEXT NOT NULL,
            model_name TEXT,
            theme_name TEXT NOT NULL DEFAULT 'synaptiq',
            collage_id INTEGER REFERENCES collages(id),
            status TEXT NOT NULL DEFAULT 'drafting',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE session_variants (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES authoring_sessions(id) ON DELETE CASCADE,
            variant_index INTEGER NOT NULL,
            html_storage_path TEXT NOT NULL,
            layout_config JSONB,
            color_config JSONB,
            selected BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE session_feedback (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES authoring_sessions(id) ON DELETE CASCADE,
            variant_id INTEGER NOT NULL REFERENCES session_variants(id),
            feedback_text TEXT NOT NULL,
            revision_number INTEGER NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX idx_session_variants_session_id ON session_variants(session_id);
        CREATE INDEX idx_session_feedback_session_id ON session_feedback(session_id);
        CREATE INDEX idx_authoring_sessions_status ON authoring_sessions(status);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS session_feedback;
        DROP TABLE IF EXISTS session_variants;
        DROP TABLE IF EXISTS authoring_sessions;
        DROP TABLE IF EXISTS collages;
    """)
