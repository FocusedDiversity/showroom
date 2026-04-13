"""
Layout Collection Registry — named layout packages for deck generation.

Each layout collection defines a template directory (17 slide type templates
+ shell) and style metadata (border-radius, spacing, shadows, etc.).
Fonts and colors are provided independently via FontPairing and Palette.
"""

from dataclasses import dataclass, field


@dataclass
class Layout:
    name: str
    slug: str
    description: str
    template_dir: str         # Relative path under templates/ to layout's templates
    style_metadata: dict = field(default_factory=dict)

    def to_metadata(self):
        """Return a dict of layout metadata for use in templates."""
        return {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'template_dir': self.template_dir,
            **self.style_metadata,
        }


# ── Built-in Layout Collections ──────────────────────────────────────

EDITORIAL = Layout(
    name='Editorial',
    slug='editorial',
    description='Clean editorial feel — generous whitespace, thin accent lines, subtle shadows',
    template_dir='authoring/layouts/editorial',
    style_metadata={
        'border_radius': '16px',
        'border_radius_sm': '12px',
        'card_padding': '32px 28px',
        'top_bar_height': '4px',
        'title_size': '52px',
        'h1_size': '34px',
        'body_size': '16px',
        'shadow': '0 1px 3px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.03)',
        'accent_width': '6px',
    },
)

BOLD = Layout(
    name='Bold',
    slug='bold',
    description='High-contrast — strong dividers, square corners, compact spacing',
    template_dir='authoring/layouts/bold',
    style_metadata={
        'border_radius': '4px',
        'border_radius_sm': '4px',
        'card_padding': '28px 24px',
        'top_bar_height': '6px',
        'title_size': '58px',
        'h1_size': '38px',
        'body_size': '16px',
        'shadow': '0 2px 4px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.06)',
        'accent_width': '8px',
    },
)

ELEGANT = Layout(
    name='Elegant',
    slug='elegant',
    description='Premium consulting feel — rounded shapes, generous spacing, soft shadows',
    template_dir='authoring/layouts/elegant',
    style_metadata={
        'border_radius': '24px',
        'border_radius_sm': '20px',
        'card_padding': '36px 32px',
        'top_bar_height': '3px',
        'title_size': '64px',
        'h1_size': '32px',
        'body_size': '15px',
        'shadow': '0 1px 2px rgba(0,0,0,0.03), 0 12px 32px rgba(0,0,0,0.025)',
        'accent_width': '4px',
    },
)

_LAYOUTS = {
    'editorial': EDITORIAL,
    'bold': BOLD,
    'elegant': ELEGANT,
}

# Map base layout slugs to their template directories
_BASE_TEMPLATE_DIRS = {
    'editorial': 'authoring/layouts/editorial',
    'bold': 'authoring/layouts/bold',
    'elegant': 'authoring/layouts/elegant',
}


def _row_to_layout(row):
    """Reconstruct a Layout from a custom_layouts DB row."""
    import json
    data = row['layout_data']
    if isinstance(data, str):
        data = json.loads(data)
    base_slug = row.get('base_layout_slug', 'editorial')
    template_dir = _BASE_TEMPLATE_DIRS.get(base_slug, 'authoring/layouts/editorial')
    return Layout(
        name=row['name'],
        slug=row['slug'],
        description=row.get('description', ''),
        template_dir=template_dir,
        style_metadata=data.get('style_metadata', {}),
    )


def list_layouts(db=None):
    """Return all available layouts (built-in + custom from DB)."""
    result = list(_LAYOUTS.values())
    if db:
        rows = db.execute(
            'SELECT * FROM custom_layouts ORDER BY name'
        ).fetchall()
        for row in rows:
            result.append(_row_to_layout(row))
    return result


def get_layout(slug='editorial', db=None):
    """Get a layout by slug. Checks built-in first, then DB. Falls back to Editorial."""
    if slug in _LAYOUTS:
        return _LAYOUTS[slug]
    if db:
        row = db.execute(
            'SELECT * FROM custom_layouts WHERE slug = %s', (slug,)
        ).fetchone()
        if row:
            return _row_to_layout(row)
    return EDITORIAL
