"""
Deck Generator — assembles slides, theme, and collage into a self-contained HTML deck.

Takes a list of Slide objects from the parser, a Theme from the theme engine,
and an optional collage image (data URI or path), and produces a complete
HTML file using the deck_shell.html + slide templates.
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
            # Try to split on colon or dash for title/body
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
        # Match patterns like "$1.2M revenue impact" or "95% accuracy"
        m = re.match(r'^([\$€£]?[\d,.]+[%xX+]?[\w]*)\s+(.+)$', line)
        if m:
            stats.append({
                'value': m.group(1),
                'label': m.group(2),
                'description': '',
            })
        else:
            # Try to use the whole line as a stat
            stats.append({'value': line, 'label': '', 'description': ''})

    return stats


def _parse_timeline_from_body(body_text):
    """Parse timeline phases from body text."""
    phases = []
    lines = [l.strip() for l in body_text.strip().split('\n') if l.strip()]

    for line in lines:
        # Numbered items: "1. Phase one: Description"
        m = re.match(r'^\d+[\.\)]\s+(.+)$', line)
        if m:
            text = m.group(1)
            # Try to extract weeks/timing
            weeks_match = re.match(r'(Week\s+[\d-]+|Phase\s+\w+|Month\s+[\d-]+):\s*(.+)', text, re.I)
            if weeks_match:
                phases.append({
                    'weeks': weeks_match.group(1),
                    'title': weeks_match.group(2),
                    'description': '',
                    'highlight': '',
                })
            else:
                # Split on colon
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

        # Lines with week/phase keywords
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


def render_slide(slide, slide_index, theme, collage_data_uri='', dark=False):
    """Render a single slide to HTML using the appropriate template."""
    env = _get_jinja_env()
    meta = theme.to_metadata()

    layout = slide.layout_hint
    template_name = f'authoring/slides/{layout}.html'

    # Common context
    ctx = {
        'slide_index': slide_index,
        'title': _inline_formatting(html_module.escape(slide.title)),
        'section_label': slide.section_label,
        'dark': dark,
        'logo_svg': meta['logo_svg'],
    }

    if layout == 'title':
        ctx['subtitle'] = slide.subtitle
        ctx['collage_data_uri'] = collage_data_uri
        ctx['prepared_for'] = ''  # Can be set by caller
        template = env.get_template(template_name)
        return template.render(**ctx)

    elif layout == 'cards':
        ctx['cards'] = _parse_cards_from_body(slide.body)
        template = env.get_template(template_name)
        return template.render(**ctx)

    elif layout == 'stats':
        ctx['stats'] = _parse_stats_from_body(slide.body)
        template = env.get_template(template_name)
        return template.render(**ctx)

    elif layout == 'timeline':
        ctx['phases'] = _parse_timeline_from_body(slide.body)
        template = env.get_template(template_name)
        return template.render(**ctx)

    elif layout == 'split':
        left_html, right_html = _parse_split_from_body(slide.body)
        ctx['left_html'] = left_html
        ctx['right_html'] = right_html
        template = env.get_template(template_name)
        return template.render(**ctx)

    elif layout == 'closing':
        ctx['subtitle'] = slide.subtitle or slide.body.split('\n')[0] if slide.body else ''
        ctx['body_html'] = _markdown_body_to_html(slide.body)
        ctx['cta_text'] = ''
        ctx['cta_email'] = ''
        template = env.get_template(template_name)
        return template.render(**ctx)

    else:
        # Default to text
        ctx['body_html'] = _markdown_body_to_html(slide.body)
        ctx['callout'] = ''
        template = env.get_template('authoring/slides/text.html')
        return template.render(**ctx)


def generate_deck(slides, theme, collage_data_uri='', deck_title='Untitled Deck'):
    """Generate a complete self-contained HTML deck.

    Args:
        slides: List of Slide objects from the parser
        theme: Theme object
        collage_data_uri: Base64 data URI for the title slide collage
        deck_title: Title shown in the browser tab

    Returns:
        str: Complete HTML document
    """
    env = _get_jinja_env()
    meta = theme.to_metadata()

    # Render each slide
    slides_html_parts = []
    for i, slide in enumerate(slides):
        # Alternate dark/light backgrounds (title always dark)
        if slide.is_title_slide:
            dark = True
        else:
            # Alternate: even index = light, odd = dark (after title)
            dark = (i % 2 == 0)

        slide_html = render_slide(slide, i, theme, collage_data_uri, dark)
        slides_html_parts.append(slide_html)

    slides_html = '\n'.join(slides_html_parts)

    # Make first slide active
    slides_html = slides_html.replace(
        'data-slide="0"',
        'data-slide="0" class="slide active"' if 'class="slide' not in slides_html.split('data-slide="0"')[0].split('\n')[-1] else 'data-slide="0"',
    )
    # Actually, let's do it properly
    slides_html = slides_html.replace(
        '<div class="slide s-title',
        '<div class="slide active s-title',
        1,
    )

    # Render the deck shell
    shell_template = env.get_template('authoring/deck_shell.html')

    return shell_template.render(
        deck_title=deck_title,
        font_import_css=f"@import url('{meta['font_imports']}');",
        font_body=meta['font_families']['body'],
        font_headline=meta['font_families']['headline'],
        color_soil=meta['primary_colors']['soil'],
        color_apricot=meta['primary_colors']['apricot'],
        color_arctic=meta['primary_colors']['arctic'],
        color_stone=meta['secondary_colors']['stone'],
        bg_dark=meta['background_dark'],
        bg_light=meta['background_light'],
        top_bar_gradient=meta['top_bar_gradient'],
        slides_html=slides_html,
        total_slides=len(slides),
    )
