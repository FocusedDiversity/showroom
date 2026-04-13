# Spec: PPTX Import

## Summary

Adds a `.pptx` upload flow to the authoring admin that extracts colors, fonts, style cues, and images from a PowerPoint file and creates a new custom palette and layout for use in deck generation. Custom palettes and layouts are persisted in PostgreSQL alongside the built-in ones.

## Context & Requirements

- **Existing system**: `authoring/palettes.py` (3 built-in Palette dataclass instances), `authoring/layouts.py` (3 built-in Layout dataclass instances). Both have `list_*()` and `get_*()` functions returning hardcoded objects.
- **PPTX parsing**: `python-pptx` library (MIT license, widely used) — provides access to slide masters, theme colors, font schemes, and slide images.
- **Font mapping**: PPTX fonts (e.g., Calibri, Arial, Garamond) must be mapped to Google Fonts equivalents since the generated HTML decks use Google Fonts imports.
- **Stack constraint**: Python/Flask, PostgreSQL, raw SQL, no frontend framework — consistent with existing Showroom.
- **Upload limit**: 50 MB max (same as existing deck uploads).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                Admin Browser                             │
│  /admin/author/import → Upload .pptx → Name & Save      │
└──────────────┬──────────────────────────────────────────┘
               │ POST multipart/form-data
               ▼
┌─────────────────────────────────────────────────────────┐
│  Flask App                                               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  PPTX Extractor (authoring/pptx_extract.py)        │ │
│  │  ├─ extract_colors(pptx) → color dict              │ │
│  │  ├─ extract_fonts(pptx) → font dict                │ │
│  │  ├─ extract_style(pptx) → style dict               │ │
│  │  └─ extract_images(pptx) → list of image bytes     │ │
│  └──────────┬──────────────────────────────────────────┘ │
│             ▼                                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Palette & Layout Persistence                       │ │
│  │  ├─ custom_palettes table (PostgreSQL)              │ │
│  │  ├─ custom_layouts table (PostgreSQL)               │ │
│  │  └─ palettes.py / layouts.py updated to merge       │ │
│  │     built-in + DB records in list/get functions     │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### PPTX Extractor (`authoring/pptx_extract.py`)

New module. Uses `python-pptx` to read a `.pptx` file and extract design elements.

#### `extract_colors(pptx_path) → dict`

Reads the theme color scheme from the first slide master:
- `dk1` (dark 1) → `background_dark`, `text_dark`
- `dk2` (dark 2) → `accent_secondary`
- `lt1` (light 1) → `background_light`, `text_light`
- `lt2` (light 2) → `card_bg_light`
- `accent1` → `accent_primary`, `highlight_light`
- `accent2` → `accent_secondary`
- `accent3` → `accent_tertiary`
- `accent4` → `section_label_light`
- `accent5` → `card_border_light`
- `accent6` → `section_label_dark`

Derived values:
- `text_muted` → lighten `text_dark` by 40%
- `card_border_dark` → `rgba({accent_primary}, 0.12)`
- `card_bg_dark` → `rgba({accent_primary}, 0.10)`
- `top_bar_gradient` → `linear-gradient(90deg, {accent1}, {accent2}, {accent3})`
- `highlight_dark_gradient` → `linear-gradient(135deg, {accent3}, {accent1})`

Returns a dict with all Palette field names → hex values.

#### `extract_fonts(pptx_path) → dict`

Reads the font scheme from the first slide master:
- Major font (headings) → `font_title`
- Minor font (body) → `font_content`

Returns `{'title_font': 'Calibri', 'content_font': 'Arial', ...}` (original font names).

#### `map_to_google_fonts(font_name) → dict`

Maps a PPTX font name to the closest Google Fonts equivalent. Maintains a lookup table of common mappings:

| PPTX Font | Google Font Equivalent |
|-----------|----------------------|
| Calibri | Open Sans |
| Arial | Open Sans |
| Garamond | EB Garamond |
| Georgia | Lora |
| Times New Roman | Playfair Display |
| Helvetica | Inter |
| Century Gothic | Quicksand |
| Cambria | Merriweather |
| Trebuchet MS | Source Sans 3 |
| Verdana | Nunito |
| Palatino | Libre Baskerville |
| Book Antiqua | Libre Baskerville |
| Rockwell | Zilla Slab |
| Impact | Oswald |
| Futura | Poppins |
| Gill Sans | Lato |
| Avenir | Nunito Sans |
| Myriad Pro | Source Sans 3 |
| Proxima Nova | Montserrat |
| (fallback) | Quicksand |

Returns `{'family': "'Open Sans', sans-serif", 'import_name': 'Open+Sans:wght@300;400;500;600;700'}`.

#### `extract_style(pptx_path) → dict`

Analyzes the slide master layout to infer style cues:
- Slide dimensions → aspect ratio check (should be 16:9)
- Placeholder margins/padding → approximate `card_padding`
- Rounded vs. square shape styles → `border_radius`
- Presence of strong borders vs. subtle → `accent_width`, `shadow`

Returns a `style_metadata` dict compatible with `Layout.style_metadata`. Falls back to Editorial defaults for properties that can't be inferred.

#### `extract_images(pptx_path) → list[dict]`

Extracts all embedded images from the presentation:
- Image bytes + content type + original filename
- Filters to images > 10KB (skips icons/bullets)
- Returns list of `{'data': bytes, 'filename': str, 'content_type': str}`

#### `choose_base_layout(fonts, style) → str`

Determines which existing template directory best matches the extracted style:
- Serif title font → `'editorial'` or `'elegant'`
- Display/decorative title font → `'elegant'`
- Sans-serif title font with tight spacing → `'bold'`
- Default → `'editorial'`

Returns the slug of the base layout to reuse templates from.

### Database Tables

```sql
CREATE TABLE custom_palettes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    palette_data JSONB NOT NULL,  -- All Palette fields as JSON
    source TEXT NOT NULL DEFAULT 'pptx',  -- 'pptx' or 'manual'
    source_filename TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE custom_layouts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    layout_data JSONB NOT NULL,  -- font_title, font_content, font_imports, style_metadata
    base_layout_slug TEXT NOT NULL DEFAULT 'editorial',  -- Which template dir to reuse
    source TEXT NOT NULL DEFAULT 'pptx',
    source_filename TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Registry Updates (`palettes.py`, `layouts.py`)

Update `list_palettes()` and `get_palette()` to merge built-in palettes with custom ones from the database:

```python
def list_palettes(db=None):
    """Return built-in + custom palettes."""
    result = list(_PALETTES.values())
    if db:
        rows = db.execute('SELECT * FROM custom_palettes ORDER BY name').fetchall()
        for row in rows:
            result.append(_row_to_palette(row))
    return result
```

Same pattern for `list_layouts()` / `get_layout()`. Custom layouts use the `base_layout_slug` to resolve `template_dir`.

### Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/admin/author/import` | GET | Upload form |
| `/admin/author/import` | POST | Accept .pptx, extract, show preview |
| `/admin/author/import/save` | POST | Save named palette + layout to DB |

### UI Flow

1. **Upload page** (`/admin/author/import`): Simple form with file input (`.pptx` only) and "Extract" button.
2. **Preview page** (same route, POST response): Shows extracted colors as swatches, extracted fonts as sample text, detected style properties. Two name inputs: "Palette Name" and "Layout Name". "Save & Use" button.
3. **After save**: Redirects to `/admin/author` with the new palette and layout pre-selected.

## Operational Considerations

- **python-pptx dependency**: Add `python-pptx>=0.6.23` to `requirements.txt`.
- **Font availability**: Google Fonts alternatives may not perfectly match the PPTX fonts. The mapping table covers common cases; unknown fonts fall back to Quicksand/Open Sans.
- **Theme-less PPTX files**: Some PPTX files have no theme or use default Office themes. The extractor should handle this gracefully and fall back to the built-in Arctic Breeze palette values.

## Risks & Tradeoffs

- **Color mapping accuracy**: PPTX theme colors don't map 1:1 to the Palette dataclass fields. The heuristic mapping (dk1 → background_dark, accent1 → accent_primary) works for standard Office themes but may produce odd results for heavily customized themes. Mitigation: the preview step lets the user verify before saving.
- **Font matching**: Google Fonts may not have a close equivalent for every PPTX font. Mitigation: the fallback is always a safe sans-serif; user can edit after import.
- **No new templates**: Imported layouts reuse existing template HTML (editorial/bold/elegant). This means the structural layout of slides won't change — only fonts, colors, and style metadata. This is a deliberate tradeoff for simplicity.
