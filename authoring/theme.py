"""
Theme Engine — maps a named theme to CSS, font imports, and metadata.

The default "Synaptiq" theme encodes the full brand guideline palette
(Soil, Apricot Ink, Arctic) and Google Font alternatives (Zilla Slab,
Quicksand, Herr Von Muellerhoff, Abril Fatface).
"""

from dataclasses import dataclass, field


@dataclass
class Theme:
    name: str
    # Primary palette
    primary_colors: dict = field(default_factory=dict)
    # Secondary palette
    secondary_colors: dict = field(default_factory=dict)
    # Tertiary palette
    tertiary_colors: dict = field(default_factory=dict)
    # Font configuration
    font_imports: str = ''
    font_families: dict = field(default_factory=dict)
    # Logo
    logo_svg: str = ''
    logo_placement: str = 'bottom-right'
    # Backgrounds
    background_dark: str = '#312A29'
    background_light: str = '#FAF8F5'
    # Top bar gradient
    top_bar_gradient: str = ''
    # Accent colors for slide elements
    accent_colors: list = field(default_factory=list)

    def to_css(self):
        """Generate CSS string for this theme."""
        css_parts = []

        # Font imports
        if self.font_imports:
            css_parts.append(f"@import url('{self.font_imports}');")

        # CSS custom properties
        css_parts.append(':root {')

        # Primary colors
        for name, value in self.primary_colors.items():
            css_parts.append(f'  --color-{name}: {value};')

        # Secondary colors
        for name, value in self.secondary_colors.items():
            css_parts.append(f'  --color-{name}: {value};')

        # Tertiary colors
        for name, value in self.tertiary_colors.items():
            css_parts.append(f'  --color-{name}: {value};')

        # Font families
        for role, family in self.font_families.items():
            css_parts.append(f'  --font-{role}: {family};')

        # Backgrounds
        css_parts.append(f'  --bg-dark: {self.background_dark};')
        css_parts.append(f'  --bg-light: {self.background_light};')

        css_parts.append('}')

        # Base typography
        headline = self.font_families.get('headline', 'serif')
        body = self.font_families.get('body', 'sans-serif')
        caption = self.font_families.get('caption', body)

        css_parts.append(f"""
/* ── Base Typography ── */
h1, h2 {{ font-family: {headline}; }}
body, p, li {{ font-family: {body}; }}
.section-label, .caption {{ font-family: {caption}; }}
""")

        # Top bar
        if self.top_bar_gradient:
            css_parts.append(f"""
.top-bar {{
  position: absolute; top: 0; left: 0; right: 0; height: 4px;
  background: {self.top_bar_gradient};
}}
""")

        return '\n'.join(css_parts)

    def to_metadata(self):
        """Return a dict of theme metadata for use in templates."""
        return {
            'name': self.name,
            'primary_colors': self.primary_colors,
            'secondary_colors': self.secondary_colors,
            'tertiary_colors': self.tertiary_colors,
            'font_families': self.font_families,
            'font_imports': self.font_imports,
            'logo_svg': self.logo_svg,
            'logo_placement': self.logo_placement,
            'background_dark': self.background_dark,
            'background_light': self.background_light,
            'top_bar_gradient': self.top_bar_gradient,
            'accent_colors': self.accent_colors,
        }


# ── Synaptiq Logo SVG ──────────────────────────────────────────────────

SYNAPTIQ_LOGO_SVG = '''<svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg" class="logo-svg">
  <!-- Butterfly logomark -->
  <g transform="translate(20, 10) scale(0.95)">
    <!-- Outer wing (black stroke) -->
    <ellipse cx="85" cy="95" rx="55" ry="65" fill="none" stroke="{logo_stroke}" stroke-width="3.5" transform="rotate(-15, 85, 95)"/>
    <!-- Inner wing lines -->
    <ellipse cx="75" cy="100" rx="35" ry="50" fill="none" stroke="{wing_color}" stroke-width="2.5" transform="rotate(-10, 75, 100)"/>
    <ellipse cx="90" cy="90" rx="30" ry="45" fill="none" stroke="{wing_color}" stroke-width="2.5" transform="rotate(-20, 90, 90)"/>
    <!-- Wing fill (arctic blue) -->
    <ellipse cx="100" cy="60" rx="28" ry="35" fill="{wing_fill}" opacity="0.6" transform="rotate(-25, 100, 60)"/>
    <!-- Body line -->
    <path d="M70 150 Q85 100 100 55 Q102 50 108 52" fill="none" stroke="{logo_stroke}" stroke-width="3" stroke-linecap="round"/>
    <!-- TM -->
    <text x="115" y="72" font-size="10" fill="{logo_stroke}" font-family="sans-serif">TM</text>
  </g>
  <!-- Wordmark -->
  <text x="195" y="130" font-family="'Quicksand', 'All Round Gothic', sans-serif" font-size="82" font-weight="500" fill="{wordmark_color}" letter-spacing="-1">Synaptiq</text>
  <text x="648" y="130" font-family="'Quicksand', sans-serif" font-size="18" fill="{wordmark_color}">®</text>
</svg>'''


def _synaptiq_logo(variant='dark'):
    """Generate Synaptiq logo SVG for the given variant."""
    if variant == 'dark':
        return SYNAPTIQ_LOGO_SVG.format(
            logo_stroke='#312A29',
            wing_color='#A1B8CA',
            wing_fill='#A1B8CA',
            wordmark_color='#312A29',
        )
    else:  # light/white variant
        return SYNAPTIQ_LOGO_SVG.format(
            logo_stroke='#ffffff',
            wing_color='rgba(255,255,255,0.6)',
            wing_fill='#F7CFA5',
            wordmark_color='#ffffff',
        )


# ── Built-in Themes ────────────────────────────────────────────────────

def get_synaptiq_theme():
    """Create the default Synaptiq brand theme."""
    return Theme(
        name='synaptiq',
        primary_colors={
            'soil': '#312A29',
            'apricot': '#F7CFA5',
            'arctic': '#A1B8CA',
        },
        secondary_colors={
            'mint': '#C6E1D9',
            'sky': '#B6DDED',
            'stone': '#A59B93',
            'grapefruit': '#E8DE90',
            'agave': '#6A888D',
            'fog': '#E2E1E3',
        },
        tertiary_colors={
            'hale-navy': '#494F5B',
            'pine': '#1D6E6F',
            'jasper': '#CC5E58',
            'parchment': '#F6F2D6',
            'blush': '#F1DCD0',
        },
        font_imports=(
            'https://fonts.googleapis.com/css2?'
            'family=Zilla+Slab:ital,wght@0,300;0,400;0,500;0,600;0,700'
            '&family=Quicksand:wght@300;400;500;600;700'
            '&family=Herr+Von+Muellerhoff'
            '&family=Abril+Fatface'
            '&display=swap'
        ),
        font_families={
            'headline': "'Zilla Slab', serif",
            'body': "'Quicksand', sans-serif",
            'caption': "'Quicksand', sans-serif",
            'accent-script': "'Herr Von Muellerhoff', cursive",
            'accent-display': "'Abril Fatface', serif",
        },
        logo_svg=_synaptiq_logo('light'),
        logo_placement='bottom-right',
        background_dark='#312A29',
        background_light='#FAF8F5',
        top_bar_gradient='linear-gradient(90deg, #A1B8CA, #F7CFA5, #F1DCD0)',
        accent_colors=['#A1B8CA', '#8BA8BD', '#F7CFA5'],
    )


def get_theme(name='synaptiq'):
    """Get a theme by name. Falls back to Synaptiq theme."""
    themes = {
        'synaptiq': get_synaptiq_theme,
    }
    factory = themes.get(name, get_synaptiq_theme)
    return factory()
