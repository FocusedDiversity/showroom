# Spec: Font Separation

## Summary

Extracts font pairings from the Layout dataclass into a new independent `FontPairing` concept. The user picks three dimensions when creating a deck: color palette, font pairing, and layout collection. Layout collections get a preview UI showing their slide type layouts.

## Architecture Change

**Before (2 dimensions):**
```
Palette (colors) + Layout (fonts + templates + style) → Deck
```

**After (3 dimensions):**
```
Palette (colors) + FontPairing (fonts) + LayoutCollection (templates + style) → Deck
```

## Component Details

### FontPairing Dataclass (`authoring/fonts.py`)

```python
@dataclass
class FontPairing:
    name: str               # e.g. "Modern Sans"
    slug: str               # e.g. "modern-sans"
    description: str
    font_title: str         # CSS font-family for titles, e.g. "'Abril Fatface', serif"
    font_content: str       # CSS font-family for body, e.g. "'Quicksand', sans-serif"
    font_imports: str       # Google Fonts import URL
```

**Built-in font pairings** (extracted from the current 3 layouts):

1. **Classic Serif** (`classic-serif`) — Zilla Slab titles + Quicksand body (from Editorial)
2. **Bold Display** (`bold-display`) — Abril Fatface titles + Quicksand body (from Bold)
3. **Script Accent** (`script-accent`) — Herr Von Muellerhoff titles + Zilla Slab body (from Elegant)

Functions: `list_font_pairings(db=None)`, `get_font_pairing(slug, db=None)` — same pattern as palettes/layouts, merging built-in + custom DB entries.

### Layout Dataclass Changes (`authoring/layouts.py`)

Remove `font_title`, `font_content`, `font_imports` from the `Layout` dataclass. The remaining fields:

```python
@dataclass
class Layout:
    name: str               # User-facing: "Layout Collection"
    slug: str
    description: str
    template_dir: str       # Path to the 17 slide templates + shell
    style_metadata: dict    # border-radius, spacing, shadows, accent_width, etc.
```

### Generator Changes (`authoring/generator.py`)

Change signature:
```python
def generate_deck(slides, palette, font_pairing, layout, collage_data_uri, deck_title)
```

The shell template receives:
- `font_imports` and `font_title` / `font_content` from `FontPairing`
- Colors from `Palette`
- Style metadata from `Layout`

### Database Table

```sql
CREATE TABLE custom_font_pairings (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    font_data JSONB NOT NULL,  -- {font_title, font_content, font_imports}
    source TEXT NOT NULL DEFAULT 'manual',
    source_filename TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Also update `custom_layouts.layout_data` — remove font fields from stored JSONB (or ignore them at load time).

### Authoring Form Changes

Three selectors on the right column:
1. **Color Palette** (existing) — swatches
2. **Font Pairing** (new) — shows title font name + body font name + sample text
3. **Layout Collection** (renamed from "Layout") — shows name + thumbnail previews of slide types

Hidden inputs: `palette_slug`, `font_slug`, `layout_slug`.

### Layout Collection Preview

`GET /admin/author/layouts/<slug>/preview?palette=<slug>&font=<slug>` — renders a grid of 4-6 sample slides (title, content, comparison, data-chart, timeline, closing) using the selected palette + font + this layout collection. Returned as an HTML fragment displayed in a modal or expanded preview area.

### PPTX Import Update

`extract_all()` currently returns colors, fonts, style, base_layout. The save flow should now create 3 objects:
- `custom_palettes` row (unchanged)
- `custom_font_pairings` row (new — from extracted fonts)
- `custom_layouts` row (unchanged — but font fields stripped from layout_data)

### Session Schema

```sql
ALTER TABLE authoring_sessions ADD COLUMN font_slug TEXT NOT NULL DEFAULT 'classic-serif';
```

## Risks & Tradeoffs

- **Shell template coupling:** The shell.html templates reference `{{ font_title }}` and `{{ font_content }}`. These variables now come from the FontPairing instead of the Layout. The templates don't change — only the source of the values changes in the generator.
- **Backwards compatibility:** Existing sessions have no `font_slug`. Default to `'classic-serif'` (matches the old Editorial layout's fonts).
