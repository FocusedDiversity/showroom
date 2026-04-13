"""
Deck Generator — assembles slides, palette, layout, and collage into a self-contained HTML deck.

Takes a list of Slide objects from the parser, a Palette from palettes.py,
a Layout from layouts.py, and an optional collage image (data URI), and
produces a complete HTML file using the layout's shell + slide templates.
"""

import re
import html as html_module
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')


def _get_jinja_env():
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(['html']),
    )


def _markdown_body_to_html(body_text):
    """Simple markdown-to-HTML converter for slide body content.

    Handles: paragraphs, bullet lists, numbered lists, blockquotes,
    bold, italic, H3 headings. Not a full markdown parser.
    """
    if not body_text:
        return ''

    lines = body_text.split('\n')
    html_parts = []
    in_ul = False
    in_ol = False
    in_blockquote = False
    paragraph_lines = []

    def flush_paragraph():
        if paragraph_lines:
            text = ' '.join(paragraph_lines)
            text = _inline_formatting(text)
            html_parts.append(f'<p>{text}</p>')
            paragraph_lines.clear()

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append('</ul>')
            in_ul = False
        if in_ol:
            html_parts.append('</ol>')
            in_ol = False

    for line in lines:
        stripped = line.strip()

        # Empty line — flush paragraph
        if not stripped:
            flush_paragraph()
            close_lists()
            if in_blockquote:
                html_parts.append('</blockquote>')
                in_blockquote = False
            continue

        # H3 heading
        if stripped.startswith('### '):
            flush_paragraph()
            close_lists()
            text = _inline_formatting(stripped[4:])
            html_parts.append(f'<h3>{text}</h3>')
            continue

        # Blockquote
        if stripped.startswith('> '):
            flush_paragraph()
            close_lists()
            if not in_blockquote:
                html_parts.append('<blockquote>')
                in_blockquote = True
            text = _inline_formatting(stripped[2:])
            html_parts.append(f'<p>{text}</p>')
            continue

        # Bullet list
        m = re.match(r'^[-*]\s+(.+)$', stripped)
        if m:
            flush_paragraph()
            if in_ol:
                html_parts.append('</ol>')
                in_ol = False
            if not in_ul:
                html_parts.append('<ul>')
                in_ul = True
            text = _inline_formatting(m.group(1))
            html_parts.append(f'<li>{text}</li>')
            continue

        # Numbered list
        m = re.match(r'^\d+[\.\)]\s+(.+)$', stripped)
        if m:
            flush_paragraph()
            if in_ul:
                html_parts.append('</ul>')
                in_ul = False
            if not in_ol:
                html_parts.append('<ol>')
                in_ol = True
            text = _inline_formatting(m.group(1))
            html_parts.append(f'<li>{text}</li>')
            continue

        # Regular text — accumulate into paragraph
        close_lists()
        if in_blockquote:
            html_parts.append('</blockquote>')
            in_blockquote = False
        paragraph_lines.append(stripped)

    # Flush remaining
    flush_paragraph()
    close_lists()
    if in_blockquote:
        html_parts.append('</blockquote>')

    return '\n'.join(html_parts)


def _inline_formatting(text):
    """Apply inline markdown formatting: **bold**, *italic*, `code`."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


# ── Body content parsers for specific slide types ─────────────────────

def _parse_cards_from_body(body_text):
    """Parse card data from body text with H3 headings or bullet items."""
    cards = []
    lines = body_text.strip().split('\n')

    # Try H3-based cards first
    current_card = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('### '):
            if current_card:
                cards.append(current_card)
            current_card = {'title': stripped[4:], 'body': '', 'icon': '', 'footer': ''}
        elif current_card is not None:
            if stripped:
                if current_card['body']:
                    current_card['body'] += ' '
                current_card['body'] += stripped
    if current_card:
        cards.append(current_card)

    if cards:
        return cards

    # Fall back to bullet items as cards
    for line in lines:
        stripped = line.strip()
        m = re.match(r'^[-*]\s+(.+)$', stripped)
        if m:
            text = m.group(1)
            parts = re.split(r':\s+|—\s+|–\s+', text, maxsplit=1)
            if len(parts) == 2:
                cards.append({'title': parts[0], 'body': parts[1], 'icon': '', 'footer': ''})
            else:
                cards.append({'title': '', 'body': text, 'icon': '', 'footer': ''})

    return cards


def _parse_stats_from_body(body_text):
    """Parse stat data from body text."""
    stats = []
    lines = [l.strip() for l in body_text.strip().split('\n') if l.strip()]

    for line in lines:
        m = re.match(r'^([\$€£]?[\d,.]+[%xX+]?[\w]*)\s+(.+)$', line)
        if m:
            stats.append({
                'value': m.group(1),
                'label': m.group(2),
                'description': '',
            })
        else:
            stats.append({'value': line, 'label': '', 'description': ''})

    return stats


def _parse_timeline_from_body(body_text):
    """Parse timeline phases from body text."""
    phases = []
    lines = [l.strip() for l in body_text.strip().split('\n') if l.strip()]

    for line in lines:
        m = re.match(r'^\d+[\.\)]\s+(.+)$', line)
        if m:
            text = m.group(1)
            weeks_match = re.match(r'(Week\s+[\d-]+|Phase\s+\w+|Month\s+[\d-]+):\s*(.+)', text, re.I)
            if weeks_match:
                phases.append({
                    'weeks': weeks_match.group(1),
                    'title': weeks_match.group(2),
                    'description': '',
                    'highlight': '',
                })
            else:
                parts = text.split(':', 1)
                if len(parts) == 2:
                    phases.append({
                        'weeks': '',
                        'title': parts[0].strip(),
                        'description': parts[1].strip(),
                        'highlight': '',
                    })
                else:
                    phases.append({
                        'weeks': '',
                        'title': text,
                        'description': '',
                        'highlight': '',
                    })
            continue

        m = re.match(r'(Week\s+[\d-]+|Phase\s+\w+|Month\s+[\d-]+):\s*(.+)', line, re.I)
        if m:
            phases.append({
                'weeks': m.group(1),
                'title': m.group(2),
                'description': '',
                'highlight': '',
            })

    return phases


def _parse_split_from_body(body_text):
    """Split body into left (text) and right (blockquote/image) content."""
    left_lines = []
    right_lines = []

    for line in body_text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('> ') or re.match(r'^!\[', stripped):
            right_lines.append(line)
        else:
            left_lines.append(line)

    left_html = _markdown_body_to_html('\n'.join(left_lines))
    right_html = _markdown_body_to_html('\n'.join(right_lines))
    return left_html, right_html


def _parse_comparison_from_body(body_text):
    """Parse comparison columns from body with 2 H3 headings."""
    columns = []
    current_col = None
    body_lines = []

    for line in body_text.strip().split('\n'):
        stripped = line.strip()
        if stripped.startswith('### '):
            if current_col:
                current_col['body_html'] = _markdown_body_to_html('\n'.join(body_lines))
                columns.append(current_col)
                body_lines = []
            current_col = {'title': stripped[4:], 'body_html': ''}
        elif current_col is not None:
            body_lines.append(line)

    if current_col:
        current_col['body_html'] = _markdown_body_to_html('\n'.join(body_lines))
        columns.append(current_col)

    # Fallback: if no H3s, split body in half
    if not columns:
        all_lines = body_text.strip().split('\n')
        mid = len(all_lines) // 2
        columns = [
            {'title': '', 'body_html': _markdown_body_to_html('\n'.join(all_lines[:mid]))},
            {'title': '', 'body_html': _markdown_body_to_html('\n'.join(all_lines[mid:]))},
        ]

    return columns


def _parse_quote_from_body(body_text):
    """Extract blockquote text and attribution."""
    quote_lines = []
    attribution = ''

    for line in body_text.strip().split('\n'):
        stripped = line.strip()
        if stripped.startswith('> '):
            quote_lines.append(stripped[2:])
        elif stripped.startswith('—') or stripped.startswith('--'):
            attribution = stripped.lstrip('—- ').strip()
        elif not quote_lines:
            # Before the quote — might be intro text, skip
            pass
        elif stripped:
            # After quote — try as attribution
            attribution = stripped

    quote_text = ' '.join(quote_lines) if quote_lines else body_text.strip()
    return _inline_formatting(quote_text), attribution


def _extract_items(body_text):
    """Extract bullet/numbered items for agenda, summary, etc."""
    items = []
    for line in body_text.strip().split('\n'):
        stripped = line.strip()
        m = re.match(r'^[-*]\s+(.+)$', stripped)
        if m:
            items.append(m.group(1))
            continue
        m = re.match(r'^\d+[\.\)]\s+(.+)$', stripped)
        if m:
            items.append(m.group(1))
    return items


def _parse_visual_from_body(body_text):
    """Extract image URI and caption from body."""
    image_uri = ''
    caption = ''
    other_lines = []

    for line in body_text.strip().split('\n'):
        stripped = line.strip()
        m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', stripped)
        if m:
            caption = m.group(1) or caption
            image_uri = m.group(2)
        else:
            other_lines.append(stripped)

    if not caption and other_lines:
        caption = ' '.join(l for l in other_lines if l)

    return image_uri, caption


# ── Slide rendering ──────────────────────────────────────────────────

def render_slide(slide, slide_index, palette, layout, collage_data_uri='', dark=False):
    """Render a single slide to HTML using the layout's template."""
    env = _get_jinja_env()
    palette_meta = palette.to_metadata()

    hint = slide.layout_hint
    template_path = f'{layout.template_dir}/{hint}.html'

    # Common context
    ctx = {
        'slide_index': slide_index,
        'title': _inline_formatting(html_module.escape(slide.title)),
        'section_label': slide.section_label,
        'dark': dark,
        'logo_svg': _get_logo_svg(dark),
    }

    if hint == 'title':
        ctx['subtitle'] = slide.subtitle
        ctx['collage_data_uri'] = collage_data_uri
        ctx['prepared_for'] = ''

    elif hint == 'content':
        ctx['body_html'] = _markdown_body_to_html(slide.body)
        ctx['callout'] = ''

    elif hint == 'data-chart':
        ctx['stats'] = _parse_stats_from_body(slide.body)

    elif hint == 'timeline':
        ctx['phases'] = _parse_timeline_from_body(slide.body)

    elif hint == 'split':
        left_html, right_html = _parse_split_from_body(slide.body)
        ctx['left_html'] = left_html
        ctx['right_html'] = right_html

    elif hint == 'closing':
        ctx['subtitle'] = slide.subtitle or (slide.body.split('\n')[0] if slide.body else '')
        ctx['body_html'] = _markdown_body_to_html(slide.body)
        ctx['cta_text'] = ''
        ctx['cta_email'] = ''

    elif hint == 'section-divider':
        ctx['subtitle'] = slide.subtitle or ''

    elif hint == 'agenda':
        ctx['items'] = _extract_items(slide.body) or slide.items

    elif hint == 'problem':
        ctx['body_html'] = _markdown_body_to_html(slide.body)
        ctx['headline'] = ''

    elif hint == 'key-message':
        ctx['body_html'] = _markdown_body_to_html(slide.body)

    elif hint == 'comparison':
        ctx['columns'] = _parse_comparison_from_body(slide.body)

    elif hint == 'matrix':
        ctx['quadrants'] = slide.matrix_quadrants if slide.matrix_quadrants else []

    elif hint == 'table':
        ctx['table_data'] = slide.table_data if slide.table_data else []

    elif hint == 'quote':
        quote_text, attribution = _parse_quote_from_body(slide.body)
        ctx['quote_text'] = quote_text
        ctx['attribution'] = attribution

    elif hint == 'summary':
        ctx['items'] = _extract_items(slide.body) or slide.items

    elif hint == 'cta':
        ctx['body_html'] = _markdown_body_to_html(slide.body)
        ctx['cta_text'] = ''
        ctx['cta_email'] = ''

    elif hint == 'visual':
        image_uri, caption = _parse_visual_from_body(slide.body)
        ctx['image_uri'] = image_uri
        ctx['caption'] = caption

    elif hint == 'blank':
        pass  # No content needed

    else:
        # Unknown type — fall back to content
        ctx['body_html'] = _markdown_body_to_html(slide.body)
        ctx['callout'] = ''
        template_path = f'{layout.template_dir}/content.html'

    template = env.get_template(template_path)
    return template.render(**ctx)


def generate_deck(slides, palette, font_pairing, layout, collage_data_uri='', deck_title='Untitled Deck'):
    """Generate a complete self-contained HTML deck.

    Args:
        slides: List of Slide objects from the parser
        palette: Palette object from palettes.py
        font_pairing: FontPairing object from fonts.py
        layout: Layout object from layouts.py
        collage_data_uri: Base64 data URI for the title slide collage
        deck_title: Title shown in the browser tab

    Returns:
        str: Complete HTML document
    """
    env = _get_jinja_env()

    # Render each slide
    slides_html_parts = []
    for i, slide in enumerate(slides):
        if slide.is_title_slide:
            dark = True
        else:
            dark = (i % 2 == 0)

        slide_html = render_slide(slide, i, palette, layout, collage_data_uri, dark)
        slides_html_parts.append(slide_html)

    slides_html = '\n'.join(slides_html_parts)

    # Make first slide active
    slides_html = slides_html.replace(
        '<div class="slide s-title',
        '<div class="slide active s-title',
        1,
    )

    # Render the deck shell
    shell_template = env.get_template(f'{layout.template_dir}/shell.html')

    return shell_template.render(
        deck_title=deck_title,
        # Fonts from FontPairing
        font_imports=f"@import url('{font_pairing.font_imports}');",
        font_title=font_pairing.font_title,
        font_content=font_pairing.font_content,
        # Palette colors
        bg_dark=palette.background_dark,
        bg_light=palette.background_light,
        accent_primary=palette.accent_primary,
        accent_secondary=palette.accent_secondary,
        accent_tertiary=palette.accent_tertiary,
        text_dark=palette.text_dark,
        text_light=palette.text_light,
        text_muted=palette.text_muted,
        top_bar_gradient=palette.top_bar_gradient,
        card_border_light=palette.card_border_light,
        card_border_dark=palette.card_border_dark,
        card_bg_light=palette.card_bg_light,
        card_bg_dark=palette.card_bg_dark,
        section_label_light=palette.section_label_light,
        section_label_dark=palette.section_label_dark,
        highlight_light=palette.highlight_light,
        highlight_dark_gradient=palette.highlight_dark_gradient,
        # Layout style metadata
        **layout.style_metadata,
        # Content
        slides_html=slides_html,
        total_slides=len(slides),
    )


# ── Logo SVG helper ──────────────────────────────────────────────────

_LOGO_SVG_TEMPLATE = '''<svg viewBox="0 0 800 200" xmlns="http://www.w3.org/2000/svg" class="logo-svg">
  <g transform="translate(20, 10) scale(0.95)">
    <ellipse cx="85" cy="95" rx="55" ry="65" fill="none" stroke="{logo_stroke}" stroke-width="3.5" transform="rotate(-15, 85, 95)"/>
    <ellipse cx="75" cy="100" rx="35" ry="50" fill="none" stroke="{wing_color}" stroke-width="2.5" transform="rotate(-10, 75, 100)"/>
    <ellipse cx="90" cy="90" rx="30" ry="45" fill="none" stroke="{wing_color}" stroke-width="2.5" transform="rotate(-20, 90, 90)"/>
    <ellipse cx="100" cy="60" rx="28" ry="35" fill="{wing_fill}" opacity="0.6" transform="rotate(-25, 100, 60)"/>
    <path d="M70 150 Q85 100 100 55 Q102 50 108 52" fill="none" stroke="{logo_stroke}" stroke-width="3" stroke-linecap="round"/>
    <text x="115" y="72" font-size="10" fill="{logo_stroke}" font-family="sans-serif">TM</text>
  </g>
  <text x="195" y="130" font-family="'Quicksand', 'All Round Gothic', sans-serif" font-size="82" font-weight="500" fill="{wordmark_color}" letter-spacing="-1">Synaptiq</text>
  <text x="648" y="130" font-family="'Quicksand', sans-serif" font-size="18" fill="{wordmark_color}">®</text>
</svg>'''


def _get_logo_svg(dark=False):
    """Generate Synaptiq logo SVG for dark or light slide backgrounds."""
    if dark:
        return _LOGO_SVG_TEMPLATE.format(
            logo_stroke='#ffffff',
            wing_color='rgba(255,255,255,0.6)',
            wing_fill='#F7CFA5',
            wordmark_color='#ffffff',
        )
    else:
        return _LOGO_SVG_TEMPLATE.format(
            logo_stroke='#312A29',
            wing_color='#A1B8CA',
            wing_fill='#A1B8CA',
            wordmark_color='#312A29',
        )
