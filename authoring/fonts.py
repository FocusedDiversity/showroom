"""
Font Pairing Registry — named font pairings for deck generation.

Each font pairing defines a title font and a content font (with Google Fonts
import URL). Font pairings are independent of palettes and layout collections —
any font pairing can be combined with any palette and any layout collection.
"""

import json
from dataclasses import dataclass


@dataclass
class FontPairing:
    name: str
    slug: str
    description: str
    font_title: str       # CSS font-family for slide titles
    font_content: str     # CSS font-family for body/content
    font_imports: str     # Google Fonts import URL


_GOOGLE_FONTS_BASE = 'https://fonts.googleapis.com/css2?'

CLASSIC_SERIF = FontPairing(
    name='Classic Serif',
    slug='classic-serif',
    description='Zilla Slab titles + Quicksand body — clean, editorial feel',
    font_title="'Zilla Slab', serif",
    font_content="'Quicksand', sans-serif",
    font_imports=(
        _GOOGLE_FONTS_BASE
        + 'family=Zilla+Slab:ital,wght@0,300;0,400;0,500;0,600;0,700'
        '&family=Quicksand:wght@300;400;500;600;700'
        '&family=Herr+Von+Muellerhoff'
        '&family=Abril+Fatface'
        '&display=swap'
    ),
)

BOLD_DISPLAY = FontPairing(
    name='Bold Display',
    slug='bold-display',
    description='Abril Fatface titles + Quicksand body — punchy, high-contrast',
    font_title="'Abril Fatface', serif",
    font_content="'Quicksand', sans-serif",
    font_imports=(
        _GOOGLE_FONTS_BASE
        + 'family=Abril+Fatface'
        '&family=Quicksand:wght@300;400;500;600;700'
        '&family=Zilla+Slab:wght@400;600;700'
        '&display=swap'
    ),
)

SCRIPT_ACCENT = FontPairing(
    name='Script Accent',
    slug='script-accent',
    description='Herr Von Muellerhoff titles + Zilla Slab body — premium, elegant',
    font_title="'Herr Von Muellerhoff', cursive",
    font_content="'Zilla Slab', serif",
    font_imports=(
        _GOOGLE_FONTS_BASE
        + 'family=Herr+Von+Muellerhoff'
        '&family=Zilla+Slab:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400'
        '&family=Quicksand:wght@300;400;500;600;700'
        '&display=swap'
    ),
)

_FONT_PAIRINGS = {
    'classic-serif': CLASSIC_SERIF,
    'bold-display': BOLD_DISPLAY,
    'script-accent': SCRIPT_ACCENT,
}


def _row_to_font_pairing(row):
    """Reconstruct a FontPairing from a custom_font_pairings DB row."""
    data = row['font_data']
    if isinstance(data, str):
        data = json.loads(data)
    return FontPairing(
        name=row['name'],
        slug=row['slug'],
        description=row.get('description', ''),
        font_title=data.get('font_title', "'Quicksand', sans-serif"),
        font_content=data.get('font_content', "'Quicksand', sans-serif"),
        font_imports=data.get('font_imports', ''),
    )


def list_font_pairings(db=None):
    """Return all available font pairings (built-in + custom from DB)."""
    result = list(_FONT_PAIRINGS.values())
    if db:
        rows = db.execute(
            'SELECT * FROM custom_font_pairings ORDER BY name'
        ).fetchall()
        for row in rows:
            result.append(_row_to_font_pairing(row))
    return result


def get_font_pairing(slug='classic-serif', db=None):
    """Get a font pairing by slug. Checks built-in first, then DB. Falls back to Classic Serif."""
    if slug in _FONT_PAIRINGS:
        return _FONT_PAIRINGS[slug]
    if db:
        row = db.execute(
            'SELECT * FROM custom_font_pairings WHERE slug = %s', (slug,)
        ).fetchone()
        if row:
            return _row_to_font_pairing(row)
    return CLASSIC_SERIF
