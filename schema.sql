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
