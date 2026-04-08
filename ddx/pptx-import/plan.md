# Capability Plan: PPTX Import

## Step 1: Add python-pptx Dependency [DONE]

**Build:** Add `python-pptx>=0.6.23` to `requirements.txt`. Install into the venv.

**Depends on:** Nothing

**Verify:** `python3 -c "from pptx import Presentation; print('OK')"` succeeds.

---

## Step 2: PPTX Color Extractor [DONE]

**Build:** Create `authoring/pptx_extract.py` with `extract_colors(pptx_path)`. Opens the `.pptx`, reads the theme color scheme from the first slide master (`prs.slide_masters[0].element` → theme XML → `a:clrScheme`), and maps the 12 theme color slots (dk1, dk2, lt1, lt2, accent1-6, hlink, folHlink) to Palette field names. Derive computed values (text_muted, card_border_dark, card_bg_dark, top_bar_gradient, highlight_dark_gradient). Return a dict with all Palette constructor kwargs.

Handle edge cases: no slide master, no theme, default Office theme (map to sensible defaults rather than crashing).

**Depends on:** Step 1

**Verify:** Run against a sample `.pptx` with a known custom theme. Assert the returned dict has all required Palette fields and the hex values match the theme colors visible in PowerPoint.

---

## Step 3: PPTX Font Extractor + Google Fonts Mapper [DONE]

**Build:** Add `extract_fonts(pptx_path)` to `pptx_extract.py`. Reads the font scheme from the slide master theme (`a:fontScheme` → `a:majorFont`/`a:minorFont`). Returns `{'title_font': 'Calibri', 'content_font': 'Arial'}`.

Add `map_to_google_fonts(font_name)` with a lookup dict of 20+ common PPTX → Google Fonts mappings. Returns `{'family': "'Open Sans', sans-serif", 'import_name': 'Open+Sans:wght@300;400;500;600;700', 'category': 'sans-serif'}`. Falls back to Quicksand for unknown fonts.

**Depends on:** Step 1

**Verify:** Extract fonts from a sample PPTX. Verify the Google Fonts mapping returns valid import URLs. Test with known fonts (Calibri → Open Sans, Garamond → EB Garamond) and an unknown font (falls back to Quicksand).

---

## Step 4: PPTX Style Extractor + Base Layout Chooser [DONE]

**Build:** Add `extract_style(pptx_path)` to `pptx_extract.py`. Analyzes slide master placeholders for margins/padding, shape styles for border-radius cues, and overall spacing. Returns a `style_metadata` dict compatible with `Layout.style_metadata`. Falls back to Editorial defaults for undetectable properties.

Add `choose_base_layout(title_font_category, style)` that picks the best existing template directory:
- `'serif'` title + generous spacing → `'editorial'`
- `'display'` or `'cursive'` title → `'elegant'`
- `'sans-serif'` title + compact spacing → `'bold'`
- Default → `'editorial'`

**Depends on:** Step 3 (font categories)

**Verify:** Test with PPTX files using different font styles. Verify the base layout choice is reasonable (a PPTX with Impact/Oswald title font → `'bold'`, a PPTX with Garamond title → `'editorial'`).

---

## Step 5: PPTX Image Extractor [DONE]

**Build:** Add `extract_images(pptx_path)` to `pptx_extract.py`. Iterates `prs.slides`, then each slide's `shapes`, checks for `shape.image`, extracts `image.blob` + `image.content_type`. Filters images > 10KB. Returns `[{'data': bytes, 'filename': str, 'content_type': str}]`.

**Depends on:** Step 1

**Verify:** Extract images from a sample PPTX with embedded photos. Confirm the returned list contains the expected images with correct content types. Small icons/bullets are filtered out.

---

## Step 6: Database Tables for Custom Palettes & Layouts [DONE]

**Build:** Alembic migration adding two new tables:

```sql
CREATE TABLE custom_palettes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    palette_data JSONB NOT NULL,
    source TEXT NOT NULL DEFAULT 'pptx',
    source_filename TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE custom_layouts (
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
```

**Depends on:** Nothing (can run in parallel with steps 2-5)

**Verify:** Run `venv/bin/alembic upgrade head` without errors. Confirm both tables exist.

---

## Step 7: Update Palette & Layout Registries for Custom Entries [DONE]

**Build:** Update `authoring/palettes.py`:
- Add `_row_to_palette(row)` that reconstructs a `Palette` from a `custom_palettes` DB row (deserializes `palette_data` JSONB).
- Update `list_palettes()` to accept an optional `db` parameter. When provided, query `custom_palettes` and append to the built-in list.
- Update `get_palette()` to accept an optional `db` parameter. Check built-ins first, then query DB by slug.

Same pattern for `authoring/layouts.py`:
- `_row_to_layout(row)` reconstructs a `Layout`, setting `template_dir` from the `base_layout_slug` (e.g., `'authoring/layouts/editorial'`).
- `list_layouts(db=None)` merges built-in + DB.
- `get_layout(slug, db=None)` checks built-in first, then DB.

**Depends on:** Step 6

**Verify:** Insert a test row into `custom_palettes` manually. Call `list_palettes(db)` — returns 4 palettes (3 built-in + 1 custom). Call `get_palette('test-slug', db)` — returns the custom palette.

---

## Step 8: Update Routes to Pass `db` to Registry Functions [DONE]

**Build:** Update `authoring/routes.py` — every call to `list_palettes()`, `get_palette()`, `list_layouts()`, `get_layout()` now passes the `db` connection. This is a mechanical change: add `db` as the first arg to each call.

Also update `author_form()` to pass `db` when building the palette/layout lists for the template context.

**Depends on:** Step 7

**Verify:** Start the app, navigate to `/admin/author`. The form still shows the 3 built-in palettes and 3 built-in layouts. No errors.

---

## Step 9: Import Route + Upload UI [DONE]

**Build:** Add new routes to `authoring/routes.py`:

`GET /admin/author/import` — Renders a simple upload form (`templates/admin/author_import.html`) with:
- File input accepting `.pptx` only
- "Extract Design" submit button

`POST /admin/author/import` — Accepts the uploaded `.pptx`:
1. Save to a temp file
2. Call `extract_colors()`, `extract_fonts()`, `extract_style()`, `extract_images()`
3. Map fonts to Google Fonts
4. Choose base layout
5. Render a preview/confirmation page showing:
   - Extracted color swatches (all palette fields as colored circles)
   - Font preview text in the mapped Google Fonts
   - Detected base layout
   - Extracted images as thumbnails
   - Two text inputs: "Palette Name" and "Layout Name"
   - "Save" button
6. Store extraction data in the session (or hidden form fields) for the save step.

Create `templates/admin/author_import.html` with both the upload form and the preview/save form (toggled by whether extraction data is present).

**Depends on:** Steps 2-5 (extractors), Step 8 (routes updated)

**Verify:** Navigate to `/admin/author/import`. Upload a `.pptx` file. See extracted colors, fonts, and images. Enter names. The form renders without errors.

---

## Step 10: Save Imported Palette & Layout [DONE]

**Build:** Add route:

`POST /admin/author/import/save` — Reads palette name, layout name, and extracted data from the form. Generates slugs from names. Inserts rows into `custom_palettes` and `custom_layouts`. Optionally saves extracted images to the collage library. Redirects to `/admin/author` with `?palette={slug}&layout={slug}` query params.

Update `author_form()` to read optional query params and pre-select the imported palette/layout.

**Depends on:** Step 9, Step 7

**Verify:** Complete the full flow: upload PPTX → preview → name → save. Redirected to `/admin/author`. The new palette and layout appear in the selectors and are pre-selected. Generate a deck — it uses the imported colors and fonts.

---

## Step 11: Add Import Link to Authoring Form [DONE]

**Build:** Add a small "Import from PPTX" link or button in the authoring form (`templates/admin/author.html`), next to the palette/layout selectors. Links to `/admin/author/import`.

**Depends on:** Step 10

**Verify:** The import link is visible on the authoring form. Clicking it navigates to the import page. After completing an import, the user returns to the authoring form with the new palette/layout selected.
