# Spec: Deck Authoring

## Summary

The deck authoring system adds server-side HTML deck generation to Showroom. Users provide structured markdown content, select a brand theme and title-slide collage, and the system produces 2-3 branded HTML deck variants for preview and iterative refinement. Once finalized, the deck publishes directly into Showroom's existing deck management pipeline.

## Context & Requirements

- **Existing stack**: Python/Flask, PostgreSQL, Jinja2 templates, raw SQL, Gunicorn
- **Deck format**: Self-contained HTML files (single file, inline CSS/JS, base64 or external images) — same as `Synaptiq_Deck_for_Sri_Branded.html`
- **Brand compliance**: Generated decks must adhere to Synaptiq Brand Guidelines v1.1 (colors, fonts, logo, imagery rules)
- **External dependency**: Recraft.ai API for AI-generated collage images
- **Content models**: YAML-based deliverable models in `deliverable-models/` directory, organized by function (`sales/` for discovery, quote; `delivery/` for kick-off, progress-report, strategy-deliverable)
- **Generation time**: Under 30 seconds for initial preview generation; under 15 seconds for refinement iterations
- **No new frontend framework**: Admin UI uses server-rendered Jinja2 + vanilla JS (consistent with existing Showroom admin)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Admin Browser                         │
│  Authoring Form → Preview Carousel → Refinement View    │
└──────────────┬──────────────────────────┬───────────────┘
               │ POST /admin/author/*     │ GET previews
               ▼                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Flask App (app.py)                     │
│  /admin/author/* routes                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │  Content     │  │  Theme       │  │  Collage       │ │
│  │  Parser      │  │  Engine      │  │  Manager       │ │
│  │ (md→slides)  │  │ (brand→css)  │  │ (lib+recraft)  │ │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘ │
│         │                │                   │          │
│         ▼                ▼                   ▼          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Deck Generator                       │   │
│  │  Assembles slides from parsed content, theme CSS, │   │
│  │  and collage image into self-contained HTML       │   │
│  │  using Jinja2 slide templates                     │   │
│  └──────────────────────┬───────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │           Session Store (PostgreSQL)              │   │
│  │  authoring_sessions, session_variants,            │   │
│  │  session_feedback                                 │   │
│  └──────────────────────────────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │        Existing Deck Management Pipeline          │   │
│  │  (storage abstraction, decks table, upload flow)  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
               │
               ▼ (collage generation only)
┌─────────────────────────┐
│   Recraft.ai API        │
│   POST /images/generate │
└─────────────────────────┘
```

- **Content Parser**: Converts markdown (structured by deliverable model) into a list of slide data objects (title, body, layout hint, section label).
- **Theme Engine**: Maps a named theme to CSS variables, font imports, color palette, and logo SVG. The default "Synaptiq" theme encodes the full brand guideline palette and typography.
- **Collage Manager**: Manages the collage library (stored via the existing storage abstraction) and proxies requests to Recraft.ai for AI-generated collages.
- **Deck Generator**: The core engine. Takes slide data + theme + collage and renders self-contained HTML using Jinja2 slide templates. Produces 2-3 variants by varying layout templates and color emphasis.
- **Session Store**: PostgreSQL tables tracking authoring sessions, generated variants (with their HTML stored in the storage layer), and feedback history for refinement.

## Component Details

### Content Parser (`authoring/parser.py`)

- Reads markdown input and splits into slides based on `---` horizontal rules or `## ` H2 headings.
- Each slide is parsed into: `title` (H2/H3), `body` (paragraphs, lists, blockquotes), `layout_hint` (auto-detected: "text-only", "cards", "stats", "timeline", "split"), `section_label` (from deliverable model section names).
- Deliverable model awareness: when a model is selected, the parser validates the markdown against the model's expected sections and warns on missing fields. Models are organized by function — `deliverable-models/sales/` (discovery, quote) and `deliverable-models/delivery/` (kick-off, progress-report, strategy-deliverable).
- First slide is always a title slide (H1 = deck title, subtitle from first paragraph).

### Theme Engine (`authoring/theme.py`)

- A theme is a Python dict defining: `primary_colors`, `secondary_colors`, `font_imports` (Google Fonts URL), `font_families` (headline, body, caption, accent), `logo_svg`, `logo_placement`, `top_bar_gradient`, `background_colors` (dark slides vs. light slides).
- The default Synaptiq theme:
  - Primary: Soil `#312A29`, Apricot `#F7CFA5`, Arctic `#A1B8CA`
  - Headline font: `Zilla Slab` (serif, weights 300-700)
  - Body font: `Quicksand` (sans, weights 300-700)
  - Accent fonts: `Herr Von Muellerhoff` (script), `Abril Fatface` (display)
  - Alternating slide backgrounds: dark (Soil) and light (`#FAF8F5`)
  - Top bar gradient: Arctic → Apricot → Blush
- Theme outputs a CSS string and a metadata dict consumed by slide templates.

### Collage Manager (`authoring/collage.py`)

- **Library**: Stores collage images in the existing storage abstraction under `collages/` prefix. Each collage has metadata (name, tags, dimensions) in the `collages` DB table.
- **Upload**: Admin can upload custom collage images (PNG/JPG, max 5MB).
- **Generation via Recraft.ai**: Accepts a text prompt and style preset. Calls the Recraft.ai image generation API. Returns 2-3 image options. Selected image is saved to the collage library for reuse.
- **Image embedding**: For the generated HTML deck, collage images are either base64-encoded inline or referenced as relative paths (depending on whether the deck will be a single HTML file or a ZIP).

### Deck Generator (`authoring/generator.py`)

- **Slide templates**: Jinja2 HTML templates for each layout type:
  - `title.html` — Title slide with collage, deck title, subtitle, logo, metadata
  - `text.html` — Section header or text-heavy slide
  - `cards.html` — 2-4 card grid layout (used for feature lists, comparisons)
  - `stats.html` — Key metrics with large numbers and labels
  - `timeline.html` — Ordered steps or phases
  - `split.html` — Two-column with text + visual
  - `closing.html` — Thank you / contact slide
- **Variant generation**: Produces 2-3 variants by:
  1. Varying the layout template selection for ambiguous slides
  2. Shifting color emphasis (e.g., Arctic-dominant vs. Apricot-dominant accent)
  3. Adjusting title slide collage crop/position
- **Output**: A single self-contained HTML file per variant (inline CSS, inline fonts via Google Fonts import, collage as base64 data URI).
- **Refinement**: Accepts a variant + feedback text. Uses the feedback to adjust specific properties (colors, font sizes, layout swaps, content edits) and regenerates.

### Authoring Routes (`app.py` additions)

| Route | Method | Purpose |
|-------|--------|---------|
| `/admin/author` | GET | Authoring form |
| `/admin/author` | POST | Parse content + generate previews → redirect to preview |
| `/admin/author/preview/<session_id>` | GET | Preview selection page |
| `/admin/author/preview/<session_id>/select` | POST | Select a variant → redirect to refine |
| `/admin/author/refine/<session_id>` | GET | Refinement view |
| `/admin/author/refine/<session_id>` | POST | Submit feedback → regenerate → refresh |
| `/admin/author/refine/<session_id>/publish` | POST | Publish to Showroom → redirect to deck detail |
| `/admin/author/collages` | GET | Collage gallery JSON |
| `/admin/author/collages/generate` | POST | Generate collage via Recraft.ai |
| `/admin/author/collages/upload` | POST | Upload a collage image |

## Data Model & Storage

### New Tables

```sql
CREATE TABLE authoring_sessions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    markdown_content TEXT NOT NULL,
    model_name TEXT,                    -- deliverable model used (nullable)
    theme_name TEXT NOT NULL DEFAULT 'synaptiq',
    collage_id INTEGER REFERENCES collages(id),
    status TEXT NOT NULL DEFAULT 'drafting',  -- drafting, previewing, refining, published
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE session_variants (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES authoring_sessions(id) ON DELETE CASCADE,
    variant_index INTEGER NOT NULL,     -- 0, 1, 2
    html_storage_path TEXT NOT NULL,    -- path in storage abstraction
    layout_config JSONB,               -- which layouts were used per slide
    color_config JSONB,                -- color emphasis settings
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

CREATE TABLE collages (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    tags TEXT[],
    storage_path TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'upload',  -- 'upload' or 'recraft'
    recraft_prompt TEXT,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Storage

- Generated HTML variants stored via the existing storage abstraction under `authoring/<session_id>/variant_<n>.html`.
- Collage images stored under `collages/<id>.<ext>`.
- On publish, the selected variant HTML is copied into the standard deck storage path.

## Integration Points

### Recraft.ai API

- **Endpoint**: Image generation API (REST)
- **Auth**: API key stored in environment variable `RECRAFT_API_KEY`
- **Request**: Text prompt, style preset, image dimensions (1280x720 for title slide)
- **Response**: 2-3 generated images (URLs or base64)
- **Failure handling**: If Recraft.ai is unreachable or returns an error, the user is shown an error message and can retry or select an existing collage instead. No silent fallback.
- **Rate limiting**: Respect Recraft.ai rate limits; queue requests if needed.

### Existing Showroom Systems

- **Deck creation**: On publish, the authoring system calls the same internal logic as the manual upload flow — creates a row in `decks`, stores the HTML, and returns the new deck ID.
- **Storage abstraction**: All file operations go through `storage.py` — no direct filesystem access.

## Operational Considerations

- **Session cleanup**: Unpublished sessions older than 30 days can be cleaned up via a periodic task (cron or manual).
- **Recraft.ai API key rotation**: Key stored in env var, rotated via config change + restart.
- **Monitoring**: Log collage generation requests and durations. Alert on Recraft.ai failures.
- **Migration**: New tables added via Alembic migration. No changes to existing tables.

## Risks & Tradeoffs

- **HTML generation quality**: Generated decks may not match the polish of hand-crafted ones (like the Sri deck). Mitigation: Start with the Sri deck as a reference template; iterative refinement helps close the gap.
- **Recraft.ai dependency**: Collage generation depends on an external API. Mitigation: The collage library provides a fallback — users can always use existing collages or upload their own.
- **Font licensing**: Brand guidelines specify Adobe fonts (Museo Slab, Arboria, All Round Gothic) that require licenses. Mitigation: Use the approved Google Font alternatives (Zilla Slab, Quicksand, Herr Von Muellerhoff, Abril Fatface) which are already used in the Sri deck.
- **Refinement effectiveness**: Free-form feedback may be hard to translate into precise CSS/layout changes. Mitigation: Provide quick-action buttons for common adjustments; keep refinement scope focused.
