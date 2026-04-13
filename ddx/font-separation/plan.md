# Capability Plan: Font Separation

## Step 1: [DONE] FontPairing Data Model & Registry

**Build:** Create `authoring/fonts.py` with a `FontPairing` dataclass (`name`, `slug`, `description`, `font_title`, `font_content`, `font_imports`). Define 3 built-in pairings extracted from the current layouts:

1. **Classic Serif** (`classic-serif`) — `'Zilla Slab', serif` titles + `'Quicksand', sans-serif` body (from Editorial)
2. **Bold Display** (`bold-display`) — `'Abril Fatface', serif` titles + `'Quicksand', sans-serif` body (from Bold)
3. **Script Accent** (`script-accent`) — `'Herr Von Muellerhoff', cursive` titles + `'Zilla Slab', serif` body (from Elegant)

Include `_row_to_font_pairing(row)` for DB rows, and `list_font_pairings(db=None)` / `get_font_pairing(slug, db=None)` following the same pattern as palettes.

**Depends on:** Nothing

**Verify:** `from authoring.fonts import list_font_pairings; assert len(list_font_pairings()) == 3`

---

## Step 2: [DONE] Remove Font Fields from Layout Dataclass

**Build:** Update `authoring/layouts.py`:
- Remove `font_title`, `font_content`, `font_imports` from the `Layout` dataclass.
- Remove these fields from `EDITORIAL`, `BOLD`, and `ELEGANT` constants.
- Update `_row_to_layout()` to stop reading font fields from `layout_data` JSONB.
- Update `to_metadata()` to exclude font fields.

The `Layout` now only holds: `name`, `slug`, `description`, `template_dir`, `style_metadata`.

**Depends on:** Nothing (but coordinate with Step 3)

**Verify:** `from authoring.layouts import list_layouts; l = list_layouts()[0]; assert not hasattr(l, 'font_title')`

---

## Step 3: [DONE] Update Generator to Accept FontPairing

**Build:** Change `generate_deck()` signature from `(slides, palette, layout, ...)` to `(slides, palette, font_pairing, layout, ...)`. Update the shell template rendering to:
- Take `font_imports`, `font_title`, `font_content` from `font_pairing` (not `layout`)
- Take `style_metadata` from `layout` (unchanged)
- Take colors from `palette` (unchanged)

Update `render_slide()` similarly — it doesn't use fonts directly (they're in the shell CSS), so it mainly needs the signature change.

Keep a compatibility shim `generate_deck_compat()` that creates a FontPairing from the old layout fields, for any code that still uses the old API.

**Depends on:** Step 1, Step 2

**Verify:** Generate a deck with `get_palette('arctic-breeze')`, `get_font_pairing('bold-display')`, `get_layout('editorial')` — produces a deck with Editorial layout structure but Abril Fatface titles. The font + layout are truly independent.

---

## Step 4: [DONE] Database Migration

**Build:** Alembic migration:
1. Create `custom_font_pairings` table (id, name, slug UNIQUE, description, font_data JSONB, source, source_filename, created_at).
2. Add `font_slug TEXT NOT NULL DEFAULT 'classic-serif'` to `authoring_sessions`.

**Depends on:** Nothing (can run in parallel)

**Verify:** `alembic upgrade head` succeeds. Both the new table and new column exist.

---

## Step 5: [DONE] Update Routes — Pass FontPairing Through

**Build:** Update `authoring/routes.py`:
- `author_form()` — add `font_pairings = list_font_pairings(db)` to template context.
- `author_generate()` — read `font_slug` from form, call `get_font_pairing(font_slug, db)`, pass to `generate_deck()`, store in session row.
- `preview_variants()` — read `font_slug` from session, pass font name to template.
- `apply_feedback()` — read `font_slug` from session, get font pairing, pass to `generate_deck()`.
- `palettes_list()` / `layouts_list()` — no change needed.
- Add `GET /admin/author/fonts` — JSON list of font pairings.

**Depends on:** Steps 1-3

**Verify:** Start app, hit `/admin/author/fonts` — returns JSON with 3 font pairings. The author form receives font_pairings in its context.

---

## Step 6: [DONE] Font Pairing Selector UI

**Build:** Update `templates/admin/author.html` to add a font pairing selector between the palette selector and the layout selector:
- Horizontal row of font pairing cards
- Each card shows: pairing name, title font sample text (in the actual Google Font), body font sample text
- Clicking selects it, updates hidden `font_slug` input
- Load the Google Fonts for preview via a `<link>` in the head

Also rename the "Slide Layout" section header to "Layout Collection".

**Depends on:** Step 5

**Verify:** Navigate to `/admin/author`. See three sections: Color Palette, Font Pairing, Layout Collection. Select "Bold Display" font + "Editorial" layout — they're independent. Generate a deck — titles are Abril Fatface but layout is Editorial's generous whitespace.

---

## Step 7: [DONE] Layout Collection Preview UI

**Build:** Add route `GET /admin/author/layouts/<slug>/preview` that renders a grid of 6 sample slides (title, content, comparison, data-chart, timeline, closing) using the requested layout collection + the currently selected palette and font (passed as query params `?palette=<slug>&font=<slug>`). Returns an HTML page.

Update the layout selector cards in `author.html` to include a "Preview" link/button that opens this route in a new tab or modal, passing the currently selected palette and font slugs.

**Depends on:** Step 6

**Verify:** Click "Preview" on the Editorial layout card. A new tab opens showing 6 sample slides rendered in Editorial layout with the currently selected palette and font. Switch to Bold layout preview — same colors and fonts but different card shapes, spacing, and accent styles.

---

## Step 8: [DONE] Update PPTX Import for 3 Dimensions

**Build:** Update `authoring/routes.py` PPTX import flow:
- `pptx_import()` — the preview page now shows extracted fonts as a separate section from the layout.
- `pptx_import_save()` — creates 3 DB rows: `custom_palettes`, `custom_font_pairings`, and `custom_layouts` (with font fields stripped from layout_data).
- The save redirect passes `?palette=<slug>&font=<slug>&layout=<slug>`.

Update `templates/admin/author_import.html`:
- Add a third name input: "Font Pairing Name" (between palette name and layout name).
- Show extracted fonts in their own section with clear preview.

**Depends on:** Steps 5-6

**Verify:** Upload a PPTX. See three name inputs (palette, font pairing, layout collection). Save all three. Redirected to authoring form with all three pre-selected.

---

## Step 9: [DONE] Rename "Layout" to "Layout Collection" in UI

**Build:** Sweep all user-facing strings:
- `templates/admin/author.html` — section header, card labels
- `templates/admin/author_preview.html` — meta badges
- `templates/admin/author_import.html` — section headers, name labels
- JSON API responses (`/admin/author/layouts`) — no change needed (slug stays `layout`)

Keep all code-level names (`Layout`, `layout_slug`, `get_layout`) unchanged — only change display text.

**Depends on:** Step 6

**Verify:** All UI surfaces say "Layout Collection" instead of "Layout". API slugs and code are unchanged.
