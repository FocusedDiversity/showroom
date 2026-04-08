"""
Layout Registry — named layout packages for deck generation.

Each layout defines a font pairing (title font ≠ content font), a template
directory, and style metadata. Layouts are independent of palettes — any
layout can be combined with any palette.
"""

from dataclasses import dataclass, field


@dataclass
class Layout:
    name: str
    slug: str
    description: str
    font_title: str           # CSS font-family for slide titles
    font_content: str         # CSS font-family for body/content
    font_imports: str         # Google Fonts import URL
    template_dir: str         # Relative path under templates/ to layout's templates
    style_metadata: dict = field(default_factory=dict)

    def to_metadata(self):
        """Return a dict of layout metadata for use in templates."""
        return {
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'font_title': self.font_title,
            'font_content': self.font_content,
            'font_imports': self.font_imports,
            'template_dir': self.template_dir,
            **self.style_metadata,
        }


# ── Built-in Layouts ─────────────────────────────────────────────────

_GOOGLE_FONTS_BASE = 'https://fonts.googleapis.com/css2?'

EDITORIAL = Layout(
    name='Editorial',
    slug='editorial',
    description='Clean editorial feel — Zilla Slab titles, Quicksand body, generous whitespace',
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
    description='High-contrast — Abril Fatface titles, Quicksand body, strong dividers',
    font_title="'Abril Fatface', serif",
    font_content="'Quicksand', sans-serif",
    font_imports=(
        _GOOGLE_FONTS_BASE
        + 'family=Abril+Fatface'
        '&family=Quicksand:wght@300;400;500;600;700'
        '&family=Zilla+Slab:wght@400;600;700'
        '&display=swap'
    ),
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
    description='Premium consulting feel — Herr Von Muellerhoff display, Zilla Slab body',
    font_title="'Herr Von Muellerhoff', cursive",
    font_content="'Zilla Slab', serif",
    font_imports=(
        _GOOGLE_FONTS_BASE
        + 'family=Herr+Von+Muellerhoff'
        '&family=Zilla+Slab:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400'
        '&family=Quicksand:wght@300;400;500;600;700'
        '&display=swap'
    ),
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
        font_title=data.get('font_title', "'Quicksand', sans-serif"),
        font_content=data.get('font_content', "'Quicksand', sans-serif"),
        font_imports=data.get('font_imports', ''),
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
