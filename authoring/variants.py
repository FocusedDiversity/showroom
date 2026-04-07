"""
Variant Generation — produces 2-3 deck variants from the same content.

Strategies:
1. Vary layout template selection for ambiguous slides
2. Shift color emphasis (Arctic-dominant vs Apricot-dominant)
3. Adjust title slide collage positioning
"""

import copy
import json
from authoring.parser import Slide
from authoring.theme import Theme, get_synaptiq_theme
from authoring.generator import generate_deck


# ── Variant Strategies ────────────────────────────────────────────────

def _alternate_layouts(slides):
    """Create layout alternatives for ambiguous slides."""
    alternatives = {
        'cards': ['text', 'cards'],
        'text': ['text', 'split'],
        'timeline': ['timeline', 'cards'],
    }
    alt_slides = []
    for s in slides:
        new_slide = copy.deepcopy(s)
        if s.layout_hint in alternatives:
            alts = alternatives[s.layout_hint]
            # Pick the second option (the alternative)
            new_slide.layout_hint = alts[1] if s.layout_hint == alts[0] else alts[0]
        alt_slides.append(new_slide)
    return alt_slides


def _make_color_shifted_theme(base_theme, emphasis='arctic'):
    """Create a theme variant with shifted color emphasis."""
    theme = copy.deepcopy(base_theme)

    if emphasis == 'apricot':
        # Swap accent order — apricot becomes dominant
        theme.accent_colors = ['#F7CFA5', '#A1B8CA', '#8BA8BD']
        theme.top_bar_gradient = 'linear-gradient(90deg, #F7CFA5, #A1B8CA, #F1DCD0)'
    elif emphasis == 'arctic':
        # Arctic dominant (default Synaptiq)
        theme.accent_colors = ['#A1B8CA', '#8BA8BD', '#F7CFA5']
        theme.top_bar_gradient = 'linear-gradient(90deg, #A1B8CA, #F7CFA5, #F1DCD0)'
    elif emphasis == 'warm':
        # Warm palette — blush + apricot + soil tones
        theme.accent_colors = ['#F1DCD0', '#F7CFA5', '#A59B93']
        theme.top_bar_gradient = 'linear-gradient(90deg, #F1DCD0, #F7CFA5, #A59B93)'

    return theme


VARIANT_CONFIGS = [
    {
        'name': 'Arctic Focus',
        'color_emphasis': 'arctic',
        'use_alt_layouts': False,
        'collage_position': 'right',
    },
    {
        'name': 'Apricot Focus',
        'color_emphasis': 'apricot',
        'use_alt_layouts': True,
        'collage_position': 'right',
    },
    {
        'name': 'Warm Tones',
        'color_emphasis': 'warm',
        'use_alt_layouts': False,
        'collage_position': 'right',
    },
]


def generate_variants(slides, base_theme, collage_data_uri='', deck_title='Untitled',
                      num_variants=3):
    """Generate multiple deck variants.

    Args:
        slides: List of Slide objects
        base_theme: Base Theme object
        collage_data_uri: Collage image data URI
        deck_title: Deck title
        num_variants: Number of variants to generate (2-3)

    Returns:
        list[dict]: Each dict has 'html', 'layout_config', 'color_config', 'name'
    """
    num_variants = min(num_variants, len(VARIANT_CONFIGS))
    results = []

    for i in range(num_variants):
        config = VARIANT_CONFIGS[i]

        # Apply layout variation
        if config['use_alt_layouts']:
            variant_slides = _alternate_layouts(slides)
        else:
            variant_slides = copy.deepcopy(slides)

        # Apply color variation
        variant_theme = _make_color_shifted_theme(base_theme, config['color_emphasis'])

        # Generate HTML
        html = generate_deck(
            variant_slides,
            variant_theme,
            collage_data_uri=collage_data_uri,
            deck_title=deck_title,
        )

        # Build config records
        layout_config = {
            'slides': [{'index': j, 'layout': s.layout_hint} for j, s in enumerate(variant_slides)]
        }
        color_config = {
            'emphasis': config['color_emphasis'],
            'accent_colors': variant_theme.accent_colors,
        }

        results.append({
            'html': html,
            'layout_config': layout_config,
            'color_config': color_config,
            'name': config['name'],
        })

    return results
