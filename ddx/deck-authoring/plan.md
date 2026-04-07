# Capability Plan: Deck Authoring

## Step 1: Content Parser

**Build:** The markdown-to-slides parser (`authoring/parser.py`). Takes raw markdown and a deliverable model name, splits content into slide data objects with `title`, `body`, `layout_hint`, and `section_label`. Supports `---` and `## ` as slide delimiters. Auto-detects layout hints (text-only, cards, stats, timeline, split) from content structure. First slide always treated as title slide.

**Depends on:** Nothing

**Verify:** Write unit tests that parse sample markdown (including a quote-model example) and assert correct slide count, titles, body content, and layout hints. Run `python -m pytest tests/test_parser.py`.

---

## Step 2: Theme Engine

**Build:** The theme system (`authoring/theme.py`). Define a `Theme` dataclass with primary/secondary/tertiary colors, font imports, font families, logo SVG, background colors, and top-bar gradient. Implement the default "Synaptiq" theme encoding the full brand guideline palette (Soil #312A29, Apricot #F7CFA5, Arctic #A1B8CA, etc.) and Google Font alternatives (Zilla Slab, Quicksand, Herr Von Muellerhoff, Abril Fatface). Theme outputs a CSS string and a metadata dict.

**Depends on:** Nothing

**Verify:** Instantiate the Synaptiq theme, call `theme.to_css()` and verify it contains correct hex colors, font-family declarations, and Google Fonts import URL. Unit test in `tests/test_theme.py`.

---

## Step 3: Slide Templates

**Build:** Jinja2 HTML templates for each slide layout type in `templates/authoring/slides/`: `title.html`, `text.html`, `cards.html`, `stats.html`, `timeline.html`, `split.html`, `closing.html`. Each template receives slide data + theme CSS + theme metadata and renders a complete `<div class="slide">` block. Use the Sri deck (`Synaptiq_Deck_for_Sri_Branded.html`) as the reference for visual structure, spacing, and class naming.

**Depends on:** Step 1 (slide data structure), Step 2 (theme CSS/metadata)

**Verify:** Render each template with sample data and the Synaptiq theme. Open the output HTML in a browser and visually confirm it matches the style of the Sri deck (colors, fonts, layout). No automated test — visual check.

---

## Step 4: Deck Generator — Single Variant

**Build:** The core deck generator (`authoring/generator.py`). Takes a list of slide data objects, a theme, and a collage image path/data-URI. Assembles a complete self-contained HTML file: DOCTYPE, head (with font imports, inline CSS from theme), body (nav bar, deck container, slide divs rendered from templates), and inline JS for slide navigation. Use the Sri deck's nav bar and deck structure as the reference.

**Depends on:** Step 1, Step 2, Step 3

**Verify:** Generate a full deck from a sample markdown file using the Synaptiq theme and a placeholder collage image. Open in browser — slides should navigate with arrow keys and nav buttons, title slide shows the collage, all slides use correct branding.

---

## Step 5: Database Schema & Migrations

**Build:** Alembic migration adding four new tables: `collages`, `authoring_sessions`, `session_variants`, `session_feedback`. Use the schema from the spec. Run migration with `venv/bin/alembic upgrade head`.

**Depends on:** Nothing (can run in parallel with steps 1-4)

**Verify:** Run `venv/bin/alembic upgrade head` without errors. Connect to PostgreSQL and confirm all four tables exist with correct columns and constraints.

---

## Step 6: Collage Manager — Library & Upload

**Build:** Collage manager (`authoring/collage.py`) with functions to: list collages (with filtering by tags), get a single collage, upload a new collage image (validates format/size, stores via storage abstraction, inserts into `collages` table), and get collage as base64 data URI for embedding. Add Flask routes: `GET /admin/author/collages` (JSON list), `POST /admin/author/collages/upload`.

**Depends on:** Step 5 (collages table)

**Verify:** Upload a test collage image via the API endpoint. Confirm it appears in the collage list endpoint. Confirm the image is stored correctly via the storage abstraction.

---

## Step 7: Collage Manager — Recraft.ai Integration

**Build:** Add Recraft.ai API integration to the collage manager. Function `generate_collage(prompt, style_preset)` calls the Recraft.ai image generation API with the given prompt, requests 1280x720 images, and returns 2-3 image results. Selected image gets saved to the collage library. Add Flask route: `POST /admin/author/collages/generate`. API key from `RECRAFT_API_KEY` env var. Handle errors gracefully (return error message, don't crash).

**Depends on:** Step 6 (collage library infrastructure)

**Verify:** Set `RECRAFT_API_KEY` in env. Call the generate endpoint with a test prompt (e.g., "Nature and technology, botanical elements"). Confirm 2-3 images are returned. Select one and confirm it's saved to the collage library.

---

## Step 8: Variant Generation

**Build:** Extend the deck generator to produce 2-3 variants from the same content. Variant strategies: (1) vary layout template selection for ambiguous slides (e.g., a list could be `cards.html` or `text.html`), (2) shift color emphasis (Arctic-dominant vs. Apricot-dominant accents), (3) adjust title slide collage positioning (left-aligned vs. right-aligned vs. full-bleed). Each variant gets a `layout_config` and `color_config` JSON object describing its choices.

**Depends on:** Step 4 (single variant generation)

**Verify:** Generate 3 variants from the same markdown input. Open all three in a browser — they should look noticeably different in layout and color emphasis while all staying brand-compliant.

---

## Step 9: Authoring Session Routes & Form UI

**Build:** Admin routes and Jinja2 templates for the authoring entry form (`/admin/author`). Template includes: deliverable model dropdown (populated from `deliverable-models/` directory), markdown textarea with model template pre-fill, theme dropdown (hardcoded to "Synaptiq" for now), collage selection area (gallery modal + generate panel). POST handler: parses content, creates an `authoring_sessions` row, generates 2-3 variants (stored via storage abstraction, tracked in `session_variants`), redirects to preview page.

**Depends on:** Step 1, Step 2, Step 4, Step 5, Step 6, Step 8

**Verify:** Navigate to `/admin/author`. Select the "quote" model — textarea fills with template. Paste sample markdown. Select an existing collage. Click "Generate Previews" — after loading, redirected to preview page showing 2-3 deck thumbnails.

---

## Step 10: Preview Selection UI

**Build:** Preview page (`/admin/author/preview/<session_id>`). Jinja2 template showing a horizontal carousel of generated variants. Each variant shows the first 3 slides as thumbnails (rendered as small iframes or static screenshots). "Preview Full Deck" opens the variant HTML in a new tab. "Select This Option" POST marks the variant as selected and redirects to the refinement view.

**Depends on:** Step 9 (session and variants exist in DB)

**Verify:** From the authoring form, generate previews. On the preview page, click "Preview Full Deck" on a variant — full deck opens in new tab. Click "Select This Option" — redirected to refinement view.

---

## Step 11: Refinement View & Feedback Loop

**Build:** Refinement page (`/admin/author/refine/<session_id>`). Left panel: slide-by-slide preview of the selected variant (iframe or inline rendering). Right panel: feedback textarea, quick-action buttons (adjust colors, change layout, modify title slide, edit content). POST handler: saves feedback to `session_feedback` table, applies feedback to regenerate the variant (modifying layout_config, color_config, or content as appropriate), updates the stored HTML, refreshes the page. Show revision counter.

**Depends on:** Step 10 (variant selected), Step 4 (regeneration capability)

**Verify:** Select a variant, navigate to refinement view. Enter feedback "Make the accent color more prominent". Click "Apply Changes" — preview updates with more Apricot accents. Revision counter increments.

---

## Step 12: Publish to Showroom

**Build:** "Publish to Showroom" action on the refinement page. Shows confirmation modal (deck title, description). POST handler: reads the selected variant's HTML from storage, creates a new deck using the existing Showroom deck creation logic (inserts into `decks` table, stores HTML via storage abstraction, generates slug), updates the authoring session status to "published", redirects to `/admin/deck/<new_deck_id>`.

**Depends on:** Step 11 (refinement complete), existing deck management code in `app.py`

**Verify:** After refining a deck, click "Publish to Showroom". Fill in title and description. Confirm — redirected to deck detail page. Deck appears in the admin dashboard. Share links can be created. Deck renders correctly in the viewer.

---

## Step 13: Deliverable Model Templates

**Build:** Create deliverable model YAML files organized by function. Sales models in `deliverable-models/sales/`: `discovery.yaml` (discovery session), `design.yaml` (design proposal) — `quote.yaml` already exists. Delivery models in `deliverable-models/delivery/`: `kick-off.yaml` (project kick-off), `progress-report.yaml` (engagement progress update), `strategy-deliverable.yaml` (data/AI strategy final deliverable). Each model defines sections (with names and descriptions) that map to slide groupings. Update the content parser to load models from both subdirectories and validate markdown against model structure. The authoring form's model dropdown reads from this directory, grouped by function.

**Depends on:** Step 1 (parser), Step 9 (form UI)

**Verify:** Select "kick-off" model in the authoring form — textarea fills with kick-off template markdown (sections: Project Overview, Objectives, Team & Roles, Timeline, Success Criteria, Next Steps). Select "discovery" — fills with discovery sections. Generate a deck from each — slides are organized by the model's sections.

---

## Step 14: Admin Dashboard Integration

**Build:** Add a "Create New Deck" button/link to the existing admin dashboard (`/admin`) that navigates to `/admin/author`. Add an "Authoring Sessions" section showing in-progress sessions (status: drafting/previewing/refining) with "Resume" links. Add a visual indicator on decks that were created via authoring (vs. manual upload).

**Depends on:** Step 9, Step 12 (full authoring flow works end-to-end)

**Verify:** Admin dashboard shows "Create New Deck" button. Start an authoring session, leave it incomplete. Return to dashboard — session appears in "Authoring Sessions" with "Resume" link. Published authored decks show an "Authored" badge.
