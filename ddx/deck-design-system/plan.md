# Capability Plan: Deck Design System

## Step 1: Color Palette Data Model & Registry [DONE]

**Build:** Create `authoring/palettes.py` with a `Palette` dataclass holding all color assignments (backgrounds, accents, text, gradients, card colors, section labels). Implement `list_palettes()` and `get_palette(slug)` functions. Define 3 initial palettes as Python constants (no YAML files yet — keep it simple):

1. **Arctic Breeze** (`arctic-breeze`) — Arctic blue dominant. Cool, professional. Primary accent: Arctic (#A1B8CA). Gradient: Arctic → Apricot → Blush.
2. **Warm Apricot** (`warm-apricot`) — Apricot/blush dominant. Warm, inviting. Primary accent: Apricot (#F7CFA5). Gradient: Apricot → Blush → Stone.
3. **Deep Soil** (`deep-soil`) — Soil/navy dominant. Bold, authoritative. Primary accent: Hale Navy (#494F5B). Gradient: Hale Navy → Pine → Apricot.

Each palette must provide `to_css_vars()` returning a dict of CSS custom property names → values, and `to_metadata()` for template rendering context.

**Depends on:** Nothing

**Verify:** Import `palettes`, call `list_palettes()` — returns 3 palettes. Call `get_palette('arctic-breeze').to_css_vars()` — returns a dict with all expected CSS variable names and valid hex values. Run `python -m pytest tests/test_palettes.py`.

---

## Step 2: Layout Data Model & Registry [DONE]

**Build:** Create `authoring/layouts.py` with a `Layout` dataclass holding the layout's font pairing (title font, content font, Google Fonts import URL), template directory path, and style metadata (border-radius scale, spacing scale, decorative element style). Implement `list_layouts()` and `get_layout(slug)` functions. Define 3 initial layouts as Python constants:

1. **Editorial** (`editorial`) — Zilla Slab titles + Quicksand body. Clean editorial feel: generous whitespace, thin accent lines, subtle shadows. Derived from the current deck aesthetic.
2. **Bold** (`bold`) — Abril Fatface titles + Quicksand body. High-contrast: large titles, strong dividers, prominent cards with heavier borders.
3. **Elegant** (`elegant`) — Herr Von Muellerhoff display headings + Zilla Slab body. Script-inflected headers, softer card shapes (higher border-radius), organic spacing.

Each layout points to a template directory: `templates/authoring/layouts/{slug}/`.

**Depends on:** Nothing

**Verify:** Import `layouts`, call `list_layouts()` — returns 3 layouts. Each has `font_title`, `font_content`, `font_imports`, `template_dir`. Run `python -m pytest tests/test_layouts.py`.

---

## Step 3: Parser — Expanded Slide Type Detection [DONE]

**Build:** Extend `parse_markdown()` in `authoring/parser.py` to detect all 17 slide types and set `layout_hint` accordingly. Add new layout hint values: `section-divider`, `agenda`, `problem`, `key-message`, `content`, `data-chart`, `comparison`, `visual`, `quote`, `summary`, `cta`, `matrix`, `table`, `blank`. Keep existing `title`, `timeline`, `closing`.

Detection priority:
1. Explicit markers (`<!-- type:matrix -->`, `<!-- blank -->`)
2. Position-based (first slide = `title`, last slide = `closing` if no explicit type)
3. Keyword-based (title contains "agenda" → `agenda`, "problem"/"challenge" → `problem`, etc.)
4. Structure-based (exactly 4 H3s → `matrix`, blockquote as primary content → `quote`, pipe-delimited rows → `table`, etc.)
5. Content analysis (≤50 words and single paragraph → `key-message`, stat values → `data-chart`)
6. Fallback: `content`

Update the `Slide` dataclass if needed to accommodate new fields (e.g., `table_data` for parsed markdown tables, `matrix_quadrants` for 2×2 grids).

**Depends on:** Nothing

**Verify:** Write test cases in `tests/test_parser_types.py` that parse sample markdown for each of the 17 slide types and assert the correct `layout_hint` is set. Include tests for explicit markers, keyword detection, and structure detection.

---

## Step 4: Base Slide Templates — Editorial Layout (Structural Types) [DONE]

**Build:** Create the `templates/authoring/layouts/editorial/` directory. Move and rename the existing 7 slide templates from `templates/authoring/slides/` into this directory, mapping to the new type names:

- `title.html` ← existing `title.html`
- `content.html` ← existing `text.html` (renamed)
- `cards.html` → removed as a separate type (cards are a layout pattern reused within content, comparison, etc.)
- `data-chart.html` ← existing `stats.html` (renamed)
- `timeline.html` ← existing `timeline.html`
- `closing.html` ← existing `closing.html`

Then create new templates for the structural slide types:
- `section-divider.html` — Large centered title, optional subtitle, full-bleed background with brand gradient or accent color. No body content.
- `agenda.html` — Numbered list items with section labels, optional timeline dots. Similar to timeline but horizontal orientation.
- `problem.html` — Two-zone layout: problem statement (large, prominent) + supporting context (smaller, secondary).
- `key-message.html` — Single centered statement in large display font, with optional supporting line below.
- `blank.html` — Empty slide with only top bar, page number, and background color.

All templates use Jinja2 variables for colors (from palette CSS vars) and fonts (from layout font families). Templates extend no base — each is self-contained HTML for a `<div class="slide …">` block (same pattern as existing templates).

**Depends on:** Step 1 (palette CSS vars), Step 2 (layout font families)

**Verify:** Render each new template with sample data and the Arctic Breeze palette + Editorial layout. Open in browser — each slide type should be visually distinct and brand-compliant. Compare title/content/data-chart/timeline/closing against existing output to confirm no visual regression.

---

## Step 5: Base Slide Templates — Editorial Layout (Data & Comparison Types) [DONE]

**Build:** Create templates in `templates/authoring/layouts/editorial/` for data-rich slide types:

- `comparison.html` — Side-by-side columns (or before/after) with H3 headers. Each column gets a card-style container with subtle differentiation (different accent color borders).
- `matrix.html` — 2×2 grid with axis labels. Four quadrant cards arranged in a grid, with row/column headers along the edges.
- `table.html` — Styled HTML table with alternating row colors, brand-colored header row, clean borders.

Also add body-content parsers in `authoring/generator.py`:
- `_parse_comparison_from_body()` — Splits body at the 2nd H3 into two columns
- `_parse_matrix_from_body()` — Extracts 4 quadrants from H3 sections, optional axis labels from body prefix
- `_parse_table_from_body()` — Converts markdown pipe-delimited table into HTML `<table>`

**Depends on:** Step 4 (editorial template directory established)

**Verify:** Parse sample markdown containing a comparison (2 H3s), a matrix (4 H3s), and a pipe-delimited table. Generate HTML slides for each — comparison shows two columns, matrix shows a 2×2 grid, table renders a styled HTML table.

---

## Step 6: Base Slide Templates — Editorial Layout (Narrative Types) [DONE]

**Build:** Create templates in `templates/authoring/layouts/editorial/` for narrative slide types:

- `quote.html` — Large blockquote with decorative quotation marks, attribution line below. Full-width centered layout.
- `summary.html` — Numbered or bulleted key takeaways in large text. Optional header. Each takeaway gets emphasis styling.
- `cta.html` — Bold recommendation headline + supporting bullets + optional CTA button/box at bottom. Action-oriented styling.
- `visual.html` — Large image area (70%+ of slide) with optional title overlay or caption below. Image via base64 data URI or placeholder.
- `split.html` ← refactored from existing `split.html` to serve as a general two-column layout (used internally by other types too).

Also add body-content parsers:
- `_parse_quote_from_body()` — Extracts blockquote text + attribution
- `_parse_summary_from_body()` — Extracts numbered/bulleted takeaway items

**Depends on:** Step 4 (editorial template directory established)

**Verify:** Parse sample markdown with a blockquote slide, a "Key Takeaways" slide, a "Recommendations" slide, and an image slide. Generate HTML — quote shows large styled blockquote, summary shows numbered takeaways, CTA shows action box, visual shows large image area.

---

## Step 7: Generator Refactor — Palette + Layout Inputs [DONE]

**Build:** Refactor `authoring/generator.py`:

- Change `generate_deck(slides, theme, …)` signature to `generate_deck(slides, palette, layout, collage_data_uri, deck_title)`.
- Template resolution: load from `templates/authoring/layouts/{layout.slug}/{slide_type}.html` instead of `templates/authoring/slides/{type}.html`.
- CSS generation: combine `palette.to_css_vars()` with layout font imports and style metadata to produce the inline `<style>` block.
- Update `render_slide()` to accept palette + layout instead of theme.
- Update `deck_shell.html` to accept palette CSS vars + layout font families as template variables (instead of hardcoded theme values).
- Add a `render_slide()` handler for each new slide type (section-divider, agenda, problem, key-message, comparison, matrix, table, quote, summary, cta, visual, blank).

Keep the old `generate_deck(slides, theme, …)` signature working temporarily via a compatibility shim that converts Theme → Palette + Layout, so existing routes don't break.

**Depends on:** Step 1, Step 2, Steps 4-6 (palettes, layouts, all editorial templates)

**Verify:** Generate a full deck from sample markdown using `get_palette('arctic-breeze')` + `get_layout('editorial')`. Open in browser — all 17 slide types render correctly. Also verify the old `generate_deck(slides, theme, …)` still works via the compatibility shim.

---

## Step 8: Bold Layout Templates [DONE]

**Build:** Create `templates/authoring/layouts/bold/` with all 17 slide type templates. The Bold layout differentiates from Editorial through:

- **Titles**: Abril Fatface (display serif) — much larger, bolder presence
- **Content**: Quicksand (same as Editorial) — familiar readability
- **Visual style**: Stronger borders (2-3px vs 1px), higher contrast backgrounds for cards (solid color fills vs subtle shadows), bolder divider lines, more prominent top bar (6px vs 4px), larger page numbers
- **Cards**: Square corners (border-radius: 4px vs 16px), solid accent-color top borders (4px), darker card backgrounds on light slides
- **Spacing**: Tighter, more compact — less whitespace, denser content

Use the Editorial templates as the starting point and modify CSS rules and decorative elements. HTML structure stays similar so palette CSS vars work identically.

**Depends on:** Step 7 (generator resolves templates from layout directory)

**Verify:** Generate the same sample deck with `get_palette('arctic-breeze')` + `get_layout('bold')`. Open in browser — slides should look noticeably different from Editorial (bigger bolder titles, square card corners, heavier borders). Also verify with `get_palette('warm-apricot')` to confirm palette independence.

---

## Step 9: Elegant Layout Templates [DONE]

**Build:** Create `templates/authoring/layouts/elegant/` with all 17 slide type templates. The Elegant layout differentiates through:

- **Titles**: Herr Von Muellerhoff (script) for display moments (title slide, section divider, closing), Zilla Slab for other slide titles
- **Content**: Zilla Slab (serif) — warmer, more literary feel than Quicksand
- **Visual style**: High border-radius (20-24px), organic shapes, softer shadows, thin hairline borders, gradient fills on cards, script-font pull quotes
- **Cards**: Rounded corners, light gradient backgrounds, delicate 1px borders with low opacity
- **Spacing**: Generous — more whitespace, more breathing room, slightly smaller content text

Again, HTML structure stays similar. Differentiation is CSS + font choices.

**Depends on:** Step 7 (generator resolves templates from layout directory)

**Verify:** Generate the same sample deck with `get_palette('deep-soil')` + `get_layout('elegant')`. Open in browser — slides should feel premium and organic (script headings, rounded cards, generous spacing). Also verify with other palettes.

---

## Step 10: Database Migration [DONE]

**Build:** Alembic migration to add `palette_slug` and `layout_slug` columns to `authoring_sessions`:

```sql
ALTER TABLE authoring_sessions
    ADD COLUMN palette_slug TEXT NOT NULL DEFAULT 'arctic-breeze',
    ADD COLUMN layout_slug TEXT NOT NULL DEFAULT 'editorial';
```

The default values ensure existing sessions map to the equivalent of the current "Arctic Focus" variant + existing template style. The `theme_name` column is kept for now (not dropped) to avoid breaking in-progress sessions.

**Depends on:** Nothing (can run in parallel with earlier steps)

**Verify:** Run `venv/bin/alembic upgrade head` without errors. Query `authoring_sessions` — existing rows have `palette_slug = 'arctic-breeze'` and `layout_slug = 'editorial'`.

---

## Step 11: Palette Preview API & UI Component [DONE]

**Build:** Add routes and a reusable UI component for palette selection:

- `GET /admin/author/palettes` — JSON list of palettes (slug, name, description, key colors for swatch rendering).
- `GET /admin/author/palettes/<slug>/preview` — Renders a single sample slide (title slide) in the given palette + the Editorial layout, returned as HTML fragment for iframe embedding.
- Jinja2 partial `templates/admin/partials/palette_selector.html` — Horizontal row of palette cards, each showing: name, color swatches (5 circles: bg-dark, bg-light, accent-primary, accent-secondary, accent-tertiary), and a small preview thumbnail. Clicking a palette highlights it and updates the live preview iframe. Uses vanilla JS (fetch + DOM manipulation).

**Depends on:** Step 1 (palette registry), Step 7 (generator can render with palette + layout)

**Verify:** Navigate to `/admin/author/palettes` — returns JSON with 3 palettes. Load `/admin/author/palettes/warm-apricot/preview` — renders a title slide in warm tones. The palette selector partial renders 3 palette cards with correct swatches.

---

## Step 12: Layout Preview API & UI Component [DONE]

**Build:** Add routes and a reusable UI component for layout selection:

- `GET /admin/author/layouts` — JSON list of layouts (slug, name, description, font pairing info).
- `GET /admin/author/layouts/<slug>/preview` — Renders 3 sample slides (title, content, data-chart) in the given layout + the currently selected palette (passed as query param `?palette=arctic-breeze`), returned as HTML fragment.
- Jinja2 partial `templates/admin/partials/layout_selector.html` — Horizontal row of layout cards, each showing: name, font pairing description (e.g., "Abril Fatface + Quicksand"), and 3 small slide thumbnails. Clicking a layout highlights it and updates the preview. Uses vanilla JS.

**Depends on:** Step 2 (layout registry), Step 7 (generator), Steps 8-9 (all layout templates exist)

**Verify:** Load `/admin/author/layouts/bold/preview?palette=arctic-breeze` — renders 3 slides in Bold layout with Arctic Breeze colors. The layout selector partial renders 3 layout cards with correct font labels and thumbnail previews.

---

## Step 13: Authoring Form Integration [DONE]

**Build:** Update `templates/admin/author.html` and `authoring/routes.py` to replace the old variant-generation flow:

1. **Form changes**: Add the palette selector and layout selector components to the authoring form (right column, replacing the theme dropdown). The form now has: model dropdown, markdown textarea, collage selector, **palette selector**, **layout selector**, and "Generate Deck" button.
2. **POST handler** (`author_generate`): Reads `palette_slug` and `layout_slug` from form data. Creates an `authoring_sessions` row with these values. Calls `generate_deck(slides, palette, layout, …)` to produce a **single** deck (not 3 variants). Stores the HTML as a single `session_variant` row. Redirects to the preview page.
3. **Preview page**: Shows the single generated deck for full review (all slides). No more variant carousel — just "Looks Good → Refine or Publish". User can go back and change palette/layout if they want a different combination.
4. **Refinement**: Works the same as before — feedback loop regenerates using the selected palette + layout.

**Depends on:** Steps 10-12 (database, palette UI, layout UI)

**Verify:** Navigate to `/admin/author`. See palette selector with 3 options and layout selector with 3 options. Select "Warm Apricot" + "Bold". Enter sample markdown. Click "Generate Deck" — preview shows a single deck in warm tones with bold styling. Change to "Deep Soil" + "Elegant" — generates a different-looking deck.

---

## Step 14: Clean Up Legacy Variant System [DONE]

**Build:** Remove the old variant system and consolidate:

- Delete `authoring/variants.py` (the `generate_variants` function and `VARIANT_CONFIGS`).
- Remove variant-related imports from `authoring/routes.py`.
- Move the old `templates/authoring/slides/` directory to a backup or delete it (all templates now live under `templates/authoring/layouts/`).
- Update `authoring/routes.py`: remove the multi-variant generation logic from `author_generate`. Remove the variant selection step from the preview flow (no more "Select This Option" — there's only one variant now).
- Remove the compatibility shim from the generator (Step 7) — the old `generate_deck(slides, theme, …)` signature is no longer needed.
- Update `authoring/theme.py`: keep for backwards compatibility with existing published decks, but it's no longer used in new sessions.

**Depends on:** Step 13 (new flow is working end-to-end)

**Verify:** The old variant flow is gone. No imports of `variants.py` remain. Generate a deck, refine it, publish it — full flow works with palette + layout selection. Existing published decks still render correctly (they're self-contained HTML, so this is automatic).
