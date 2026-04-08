"""
Color Palette Registry — named combinations of brand colors for deck generation.

Each palette is a set of CSS color assignments derived from the Synaptiq brand
guideline. Palettes are independent of layouts — any palette can be combined
with any layout.
"""

from dataclasses import dataclass


@dataclass
class Palette:
    name: str
    slug: str
    description: str
    # Backgrounds
    background_dark: str
    background_light: str
    # Accent colors
    accent_primary: str
    accent_secondary: str
    accent_tertiary: str
    # Text
    text_dark: str       # Text on light backgrounds
    text_light: str      # Text on dark backgrounds
    text_muted: str      # Secondary/muted text
    # Gradients & decorative
    top_bar_gradient: str
    card_border_light: str
    card_border_dark: str
    card_bg_light: str
    card_bg_dark: str
    # Section labels
    section_label_light: str
    section_label_dark: str
    # Stat/highlight color
    highlight_light: str
    highlight_dark_gradient: str

    def to_css_vars(self):
        """Return a dict of CSS custom property names to values."""
        return {
            '--bg-dark': self.background_dark,
            '--bg-light': self.background_light,
            '--accent-primary': self.accent_primary,
            '--accent-secondary': self.accent_secondary,
            '--accent-tertiary': self.accent_tertiary,
            '--text-dark': self.text_dark,
            '--text-light': self.text_light,
            '--text-muted': self.text_muted,
            '--top-bar-gradient': self.top_bar_gradient,
            '--card-border-light': self.card_border_light,
            '--card-border-dark': self.card_border_dark,
            '--card-bg-light': self.card_bg_light,
            '--card-bg-dark': self.card_bg_dark,
            '--section-label-light': self.section_label_light,
            '--section-label-dark': self.section_label_dark,
            '--highlight-light': self.highlight_light,
            '--highlight-dark-gradient': self.highlight_dark_gradient,
        }

    def to_metadata(self):
        """Return a dict of palette metadata for use in templates."""
        return {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            **self.to_css_vars(),
        }


# ── Built-in Palettes ────────────────────────────────────────────────

ARCTIC_BREEZE = Palette(
    name='Arctic Breeze',
    slug='arctic-breeze',
    description='Cool, professional — Arctic blue dominant with apricot accents',
    background_dark='#312A29',
    background_light='#FAF8F5',
    accent_primary='#A1B8CA',
    accent_secondary='#8BA8BD',
    accent_tertiary='#F7CFA5',
    text_dark='#312A29',
    text_light='#ffffff',
    text_muted='#A59B93',
    top_bar_gradient='linear-gradient(90deg, #A1B8CA, #F7CFA5, #F1DCD0)',
    card_border_light='#E2DFDB',
    card_border_dark='rgba(255,255,255,0.06)',
    card_bg_light='#ffffff',
    card_bg_dark='rgba(161,184,202,0.12)',
    section_label_light='#8BA8BD',
    section_label_dark='#F7CFA5',
    highlight_light='#A1B8CA',
    highlight_dark_gradient='linear-gradient(135deg, #F7CFA5, #A1B8CA)',
)

WARM_APRICOT = Palette(
    name='Warm Apricot',
    slug='warm-apricot',
    description='Warm, inviting — Apricot and blush dominant with jasper accents',
    background_dark='#3D2E2A',
    background_light='#FBF7F3',
    accent_primary='#F7CFA5',
    accent_secondary='#F1DCD0',
    accent_tertiary='#CC5E58',
    text_dark='#312A29',
    text_light='#ffffff',
    text_muted='#A59B93',
    top_bar_gradient='linear-gradient(90deg, #F7CFA5, #F1DCD0, #A59B93)',
    card_border_light='#E8DDD6',
    card_border_dark='rgba(247,207,165,0.12)',
    card_bg_light='#ffffff',
    card_bg_dark='rgba(247,207,165,0.08)',
    section_label_light='#CC5E58',
    section_label_dark='#F7CFA5',
    highlight_light='#CC5E58',
    highlight_dark_gradient='linear-gradient(135deg, #F7CFA5, #CC5E58)',
)

DEEP_SOIL = Palette(
    name='Deep Soil',
    slug='deep-soil',
    description='Bold, authoritative — Hale Navy and pine dominant with apricot accents',
    background_dark='#494F5B',
    background_light='#F4F3F1',
    accent_primary='#1D6E6F',
    accent_secondary='#494F5B',
    accent_tertiary='#F7CFA5',
    text_dark='#312A29',
    text_light='#ffffff',
    text_muted='#7A7572',
    top_bar_gradient='linear-gradient(90deg, #494F5B, #1D6E6F, #F7CFA5)',
    card_border_light='#D8D6D3',
    card_border_dark='rgba(29,110,111,0.15)',
    card_bg_light='#ffffff',
    card_bg_dark='rgba(29,110,111,0.10)',
    section_label_light='#1D6E6F',
    section_label_dark='#F7CFA5',
    highlight_light='#1D6E6F',
    highlight_dark_gradient='linear-gradient(135deg, #F7CFA5, #1D6E6F)',
)

_PALETTES = {
    'arctic-breeze': ARCTIC_BREEZE,
    'warm-apricot': WARM_APRICOT,
    'deep-soil': DEEP_SOIL,
}


def _row_to_palette(row):
    """Reconstruct a Palette from a custom_palettes DB row."""
    import json
    data = row['palette_data']
    if isinstance(data, str):
        data = json.loads(data)
    return Palette(
        name=row['name'],
        slug=row['slug'],
        description=row.get('description', ''),
        **data,
    )


def list_palettes(db=None):
    """Return all available palettes (built-in + custom from DB)."""
    result = list(_PALETTES.values())
    if db:
        rows = db.execute(
            'SELECT * FROM custom_palettes ORDER BY name'
        ).fetchall()
        for row in rows:
            result.append(_row_to_palette(row))
    return result


def get_palette(slug='arctic-breeze', db=None):
    """Get a palette by slug. Checks built-in first, then DB. Falls back to Arctic Breeze."""
    if slug in _PALETTES:
        return _PALETTES[slug]
    if db:
        row = db.execute(
            'SELECT * FROM custom_palettes WHERE slug = %s', (slug,)
        ).fetchone()
        if row:
            return _row_to_palette(row)
    return ARCTIC_BREEZE
