# Spec: Deck Design System

## Summary

Refactors the deck authoring system to separate color palettes from slide layouts into two independently selectable dimensions. Expands slide templates from 7 to 17 types. Users preview and choose one palette + one layout before generating their deck.

## Context & Requirements

- **Existing system**: `authoring/` package with parser, theme, generator, variants, collage, routes
- **Current limitation**: Variants bundle color + layout into 3 fixed combinations
- **Target**: ≥3 palettes × ≥3 layouts = ≥9 combinations, with 17 slide types each
- **Stack constraint**: Same as existing — Python/Flask, Jinja2 templates, PostgreSQL, raw SQL, no frontend framework
- **Backwards compatibility**: Existing authored decks remain unchanged. New sessions use the palette/layout selector.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       Admin Browser                              │
│  Authoring Form → Palette Preview → Layout Preview → Generate   │
└──────────────┬──────────────────────────────────┬───────────────┘
               │ POST /admin/author/*             │ GET previews
               ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask App                                   │
│                                                                  │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐  │
│  │  Palette      │  │  Layout        │  │  Content Parser      │  │
│  │  Registry     │  │  Registry      │  │  (17 slide types)    │  │
│  │  (YAML defs)  │  │  (YAML defs +  │  │                      │  │
│  │               │  │   templates)   │  │                      │  │
│  └──────┬───────┘  └──────┬────────┘  └──────────┬───────────┘  │
│         │                 │                       │              │
│         ▼                 ▼                       ▼              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Deck Generator (refactored)                  │   │
│  │  Accepts: slides + palette + layout + collage             │   │
│  │  Resolves: templates from layout, colors from palette     │   │
│  │  Outputs: self-contained HTML                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Color Palette Registry (`authoring/palettes.py`)

Each palette is a named set of CSS color assignments derived from the Synaptiq brand guideline:

```python
@dataclass
class Palette:
    name: str                  # e.g. "Arctic Breeze"
    slug: str                  # e.g. "arctic-breeze"
    description: str
    background_dark: str       # Dark slide background
    background_light: str      # Light slide background
    accent_primary: str        # Primary accent (gradients, highlights)
    accent_secondary: str      # Secondary accent
    accent_tertiary: str       # Tertiary accent
    text_dark: str             # Text on light backgrounds
    text_light: str            # Text on dark backgrounds
    text_muted: str            # Secondary text
    top_bar_gradient: str      # CSS gradient for top bar
    card_border: str           # Card/container borders
    card_background_light: str # Card bg on light slides
    card_background_dark: str  # Card bg on dark slides
    section_label_light: str   # Section label on light slides
    section_label_dark: str    # Section label on dark slides
```

**Initial palettes** (at least 3):

1. **Arctic Breeze** — Arctic blue dominant. Cool, professional. Accents: Arctic (#A1B8CA), Sky (#B6DDED), Apricot (#F7CFA5). Gradient: Arctic → Apricot → Blush.
2. **Warm Apricot** — Apricot/blush dominant. Warm, inviting. Accents: Apricot (#F7CFA5), Blush (#F1DCD0), Jasper (#CC5E58). Gradient: Apricot → Blush → Stone.
3. **Deep Soil** — Soil/navy dominant. Bold, authoritative. Accents: Hale Navy (#494F5B), Pine (#1D6E6F), Apricot (#F7CFA5). Gradient: Hale Navy → Pine → Apricot.

Palettes are defined in YAML files under `authoring/palettes/` and loaded at startup. The `Palette` dataclass provides `to_css_vars()` returning a dict of CSS custom property names → values.

### Layout Registry (`authoring/layouts.py`)

Each layout is a named package of:
- **Font pairing**: Distinct title font + content font (from the brand's 4 font families)
- **Template directory**: A subdirectory of `templates/authoring/layouts/{slug}/` containing one Jinja2 template per slide type
- **Style metadata**: Spacing scale, border-radius, decorative element style

```python
@dataclass
class Layout:
    name: str               # e.g. "Editorial"
    slug: str               # e.g. "editorial"
    description: str
    font_title: str         # CSS font-family for slide titles
    font_content: str       # CSS font-family for body/content
    font_imports: str       # Google Fonts import URL
    template_dir: str       # Relative path to template directory
    style_metadata: dict    # Additional CSS overrides (border-radius, spacing, etc.)
```

**Initial layouts** (at least 3):

1. **Editorial** — Zilla Slab titles + Quicksand body. Clean editorial feel: generous whitespace, thin accent lines, subtle shadows. The current default aesthetic refined.
2. **Bold** — Abril Fatface titles + Quicksand body. High-contrast: large titles, strong dividers, prominent cards with heavier borders. Punchy and modern.
3. **Elegant** — Herr Von Muellerhoff display titles + Zilla Slab body. Script-inflected headers, softer card shapes, more organic spacing. Premium consulting feel.

Layouts are defined in YAML files under `authoring/layouts/` and loaded at startup. Each layout's template directory contains 17 `.html` files (one per slide type).

### Expanded Slide Types

Each layout must provide a template for all 17 slide types:

| Slide Type | Template Name | Layout Hint Detection |
|-----------|---------------|----------------------|
| Title | `title.html` | First slide (H1) |
| Section Divider | `section-divider.html` | H2 with no body content |
| Agenda / Roadmap | `agenda.html` | 3+ numbered items + "agenda"/"roadmap" keyword in title |
| Problem / Context | `problem.html` | "problem"/"challenge"/"context" keyword in title |
| Key Message | `key-message.html` | Single sentence/short paragraph body, ≤50 words |
| Content / Detail | `content.html` | Default for text-heavy slides (>50 words, mixed content) |
| Data / Chart | `data-chart.html` | Stat values detected (currency/percent) — replaces current `stats` |
| Comparison | `comparison.html` | 2 H3 headings with parallel structure, or "vs"/"compare" keyword |
| Process / Timeline | `timeline.html` | 3+ numbered items with phase/week/step keywords |
| Visual / Image | `visual.html` | Image reference (`![…]`) as primary content |
| Quote / Testimonial | `quote.html` | Blockquote (`>`) as primary content |
| Summary / Takeaway | `summary.html` | "summary"/"takeaway"/"key points" keyword in title |
| CTA / Recommendations | `cta.html` | "recommendation"/"next steps"/"call to action" keyword in title |
| 2×2 Matrix | `matrix.html` | Exactly 4 H3 headings or table-like structure with 2 axes |
| Table | `table.html` | Markdown table detected (`\|` pipe-delimited rows) |
| Closing | `closing.html` | Last slide, or "thank you"/"questions" keyword |
| Blank | `blank.html` | `<!-- blank -->` marker or empty body |

### Parser Updates (`authoring/parser.py`)

Extend `parse_markdown()` to detect the new slide types and set `layout_hint` accordingly. Detection priority (highest to lowest):
1. Explicit markers (`<!-- blank -->`, `<!-- type:matrix -->`)
2. Position-based (first slide = title, last slide = closing)
3. Keyword-based (title text contains "agenda", "problem", etc.)
4. Structure-based (4 H3s = matrix, blockquote-primary = quote, etc.)
5. Fallback: content (text-heavy default)

### Generator Refactor (`authoring/generator.py`)

- `generate_deck(slides, palette, layout, collage_data_uri, deck_title)` — now accepts a `Palette` and `Layout` instead of a `Theme`.
- Template resolution: loads from `templates/authoring/layouts/{layout.slug}/{slide_type}.html`
- CSS generation: combines palette CSS vars + layout font imports + layout style metadata
- `deck_shell.html` is shared across all layouts (parameterized by palette + layout fonts)

### Database Changes

```sql
-- Add to authoring_sessions
ALTER TABLE authoring_sessions
    ADD COLUMN palette_slug TEXT DEFAULT 'arctic-breeze',
    ADD COLUMN layout_slug TEXT DEFAULT 'editorial';

-- Drop theme_name column (replaced by palette_slug + layout_slug)
-- (deferred until old sessions are migrated)
```

`session_variants` table is retained for backwards compatibility but new sessions will only have one variant (the selected palette × layout combination). The preview flow changes from "pick 1 of 3 variants" to "pick 1 palette + pick 1 layout → generate".

### Preview Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/admin/author/palettes` | GET | JSON list of available palettes with CSS vars |
| `/admin/author/palettes/<slug>/preview` | GET | Renders a sample slide in the given palette |
| `/admin/author/layouts` | GET | JSON list of available layouts with metadata |
| `/admin/author/layouts/<slug>/preview` | GET | Renders 3 sample slides (title, content, cards) in the given layout |

### Authoring Form Changes

The authoring form (`/admin/author`) gains two new selection areas replacing the current "generate variants" flow:

1. **Palette Selector**: Horizontal row of palette swatches. Clicking one shows a live preview of a sample slide in that palette. Selected palette highlighted.
2. **Layout Selector**: Horizontal row of layout thumbnails (rendered as small preview images). Clicking one shows a larger preview of 3 sample slides. Selected layout highlighted.

The "Generate Previews" button now generates a single deck using the selected palette + layout (no more 3 variants). The preview page shows the full deck for review before publishing.

## Operational Considerations

- **Template maintenance**: 3 layouts × 17 slide types = 51 template files. To reduce duplication, templates should inherit from shared base blocks where possible (Jinja2 `{% extends %}` and `{% block %}`).
- **Adding palettes/layouts**: Both use YAML definitions — adding a new palette requires only a YAML file. Adding a new layout requires a YAML file + 17 templates.
- **Migration**: Existing sessions with `theme_name = 'synaptiq'` map to `palette_slug = 'arctic-breeze', layout_slug = 'editorial'`.

## Risks & Tradeoffs

- **Template volume**: 51 template files is significant. Mitigated by heavy use of Jinja2 inheritance and keeping structural HTML similar across layouts (differentiation via CSS, fonts, and decorative elements).
- **Layout quality**: 3 distinct layouts that all look polished requires design effort. Mitigated by deriving all 3 from the same brand guidelines and using the existing Sri deck as the baseline for "Editorial".
- **Parser accuracy**: Keyword-based slide type detection may misclassify. Mitigated by supporting explicit `<!-- type:X -->` markers as an override.
