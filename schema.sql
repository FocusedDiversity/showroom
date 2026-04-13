CREATE TABLE IF NOT EXISTS decks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS deck_assets (
    id SERIAL PRIMARY KEY,
    deck_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS share_links (
    id SERIAL PRIMARY KEY,
    deck_id INTEGER NOT NULL,
    recipient_email TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    feedback_enabled BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS views (
    id SERIAL PRIMARY KEY,
    share_link_id INTEGER NOT NULL,
    viewer_email TEXT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INTEGER DEFAULT 0,
    user_agent TEXT DEFAULT '',
    ip_address TEXT DEFAULT '',
    referrer TEXT DEFAULT '',
    is_forwarded BOOLEAN DEFAULT FALSE,
    current_slide INTEGER DEFAULT NULL,
    total_slides INTEGER DEFAULT NULL,
    FOREIGN KEY (share_link_id) REFERENCES share_links(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_share_links_token ON share_links(token);
CREATE INDEX IF NOT EXISTS idx_share_links_deck_id ON share_links(deck_id);
CREATE INDEX IF NOT EXISTS idx_views_share_link_id ON views(share_link_id);
CREATE INDEX IF NOT EXISTS idx_views_viewer_email ON views(viewer_email);
CREATE INDEX IF NOT EXISTS idx_decks_slug ON decks(slug);

-- Add columns that may be missing on existing production tables
DO $$ BEGIN
    ALTER TABLE share_links ADD COLUMN feedback_enabled BOOLEAN DEFAULT TRUE;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$ BEGIN
    ALTER TABLE views ADD COLUMN current_slide INTEGER DEFAULT NULL;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$ BEGIN
    ALTER TABLE views ADD COLUMN total_slides INTEGER DEFAULT NULL;
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS slide_feedback (
    id SERIAL PRIMARY KEY,
    view_id INTEGER NOT NULL,
    slide_number INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (view_id) REFERENCES views(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_slide_feedback_view_id ON slide_feedback(view_id);

-- Deck Authoring tables

CREATE TABLE IF NOT EXISTS collages (
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

CREATE TABLE IF NOT EXISTS authoring_sessions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    markdown_content TEXT NOT NULL,
    model_name TEXT,
    theme_name TEXT NOT NULL DEFAULT 'synaptiq',
    palette_slug TEXT NOT NULL DEFAULT 'arctic-breeze',
    font_slug TEXT NOT NULL DEFAULT 'classic-serif',
    layout_slug TEXT NOT NULL DEFAULT 'editorial',
    collage_id INTEGER REFERENCES collages(id),
    status TEXT NOT NULL DEFAULT 'drafting',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session_variants (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES authoring_sessions(id) ON DELETE CASCADE,
    variant_index INTEGER NOT NULL,
    html_storage_path TEXT NOT NULL,
    layout_config JSONB,
    color_config JSONB,
    selected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session_feedback (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES authoring_sessions(id) ON DELETE CASCADE,
    variant_id INTEGER NOT NULL REFERENCES session_variants(id),
    feedback_text TEXT NOT NULL,
    revision_number INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_variants_session_id ON session_variants(session_id);
CREATE INDEX IF NOT EXISTS idx_session_feedback_session_id ON session_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_authoring_sessions_status ON authoring_sessions(status);

-- Add columns that may be missing on existing authoring_sessions tables
DO $$ BEGIN
    ALTER TABLE authoring_sessions ADD COLUMN palette_slug TEXT NOT NULL DEFAULT 'arctic-breeze';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$ BEGIN
    ALTER TABLE authoring_sessions ADD COLUMN font_slug TEXT NOT NULL DEFAULT 'classic-serif';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;
DO $$ BEGIN
    ALTER TABLE authoring_sessions ADD COLUMN layout_slug TEXT NOT NULL DEFAULT 'editorial';
EXCEPTION WHEN duplicate_column THEN NULL;
END $$;

-- Custom design elements (PPTX import + manual)

CREATE TABLE IF NOT EXISTS custom_palettes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    palette_data JSONB NOT NULL,
    source TEXT NOT NULL DEFAULT 'pptx',
    source_filename TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS custom_font_pairings (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    font_data JSONB NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    source_filename TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS custom_layouts (
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
