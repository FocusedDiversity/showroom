"""
Content Parser — converts markdown into a list of slide data objects.

Splits on `---` horizontal rules or `## ` H2 headings. Each slide gets:
  - title: extracted from H2/H3
  - body: remaining content (paragraphs, lists, blockquotes)
  - layout_hint: auto-detected from content structure
  - section_label: from deliverable model section name (if model provided)

The first slide is always treated as a title slide (H1 = deck title).
"""

import os
import re
import yaml
from dataclasses import dataclass, field

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'deliverable-models')


@dataclass
class Slide:
    title: str = ''
    body: str = ''
    layout_hint: str = 'content'
    section_label: str = ''
    is_title_slide: bool = False
    subtitle: str = ''
    items: list = field(default_factory=list)
    table_data: list = field(default_factory=list)       # Parsed table rows
    matrix_quadrants: list = field(default_factory=list)  # 4 quadrants for 2x2 matrix


def load_model(model_name):
    """Load a deliverable model YAML file by name.

    Searches all subdirectories of deliverable-models/.
    Returns the parsed YAML dict, or None if not found.
    """
    if not model_name:
        return None

    for root, _dirs, files in os.walk(MODELS_DIR):
        for fname in files:
            if fname == f'{model_name}.yaml' or fname == f'{model_name}.yml':
                path = os.path.join(root, fname)
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
    return None


def _detect_explicit_type(body_text):
    """Check for explicit type markers like <!-- type:matrix --> or <!-- blank -->."""
    m = re.search(r'<!--\s*type:\s*(\S+)\s*-->', body_text)
    if m:
        return m.group(1).strip()
    if re.search(r'<!--\s*blank\s*-->', body_text):
        return 'blank'
    return None


def _detect_keyword_type(title):
    """Detect slide type from title keywords."""
    if not title:
        return None
    t = title.lower()

    keyword_map = [
        (['agenda', 'roadmap', 'outline', 'table of contents'], 'agenda'),
        (['problem', 'challenge', 'context', 'pain point'], 'problem'),
        (['summary', 'takeaway', 'key points', 'recap', 'in summary'], 'summary'),
        (['recommendation', 'next steps', 'call to action', 'action items'], 'cta'),
        (['thank you', 'thanks', 'questions', 'q&a', 'contact'], 'closing'),
        (['compare', 'comparison', ' vs ', 'versus', 'before and after'], 'comparison'),
    ]
    for keywords, hint in keyword_map:
        if any(kw in t for kw in keywords):
            return hint
    return None


def _has_table(body_text):
    """Check if body contains a markdown pipe-delimited table."""
    lines = [l.strip() for l in body_text.strip().split('\n') if l.strip()]
    pipe_rows = [l for l in lines if l.startswith('|') and l.endswith('|')]
    # Need at least header + separator + 1 data row
    return len(pipe_rows) >= 3


def _parse_table_data(body_text):
    """Parse a markdown pipe-delimited table into a list of lists."""
    rows = []
    for line in body_text.strip().split('\n'):
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            # Skip separator rows (---|---|---)
            if all(re.match(r'^[-:]+$', c) for c in cells):
                continue
            rows.append(cells)
    return rows


def _detect_layout_hint(title, body_text):
    """Auto-detect layout hint from title keywords and content structure.

    Returns one of the 17 slide type hints.
    """
    lines = [l.strip() for l in body_text.strip().split('\n') if l.strip()]

    # 1. Explicit markers
    explicit = _detect_explicit_type(body_text)
    if explicit:
        return explicit

    # 2. Keyword-based detection from title
    keyword_hint = _detect_keyword_type(title)
    if keyword_hint:
        return keyword_hint

    # 3. Empty/minimal body → section-divider or blank
    if not lines:
        return 'section-divider'

    # 4. Table detection (pipe-delimited rows)
    if _has_table(body_text):
        return 'table'

    # 5. H3 headings analysis
    h3_count = sum(1 for l in lines if l.startswith('### '))
    # Exactly 4 H3s → 2x2 matrix
    if h3_count == 4:
        return 'matrix'
    # 2 H3s with parallel structure → comparison
    if h3_count == 2:
        return 'comparison'

    # 6. Blockquote as primary content → quote
    blockquote_lines = [l for l in lines if l.startswith('> ')]
    non_blockquote = [l for l in lines if not l.startswith('> ')]
    if blockquote_lines and len(blockquote_lines) >= len(non_blockquote):
        return 'quote'

    # 7. Image as primary content → visual
    image_lines = [l for l in lines if re.match(r'!\[', l)]
    non_image = [l for l in lines if not re.match(r'!\[', l)]
    if image_lines and len(non_image) <= 2:
        return 'visual'

    # 8. Timeline: numbered list items or phase/step/week keywords
    numbered_count = sum(1 for l in lines if re.match(r'^\d+[\.\)]\s', l))
    timeline_keywords = sum(1 for l in lines
                           if re.search(r'\b(phase|step|week|stage|month|day)\b', l, re.I))
    if numbered_count >= 3 or timeline_keywords >= 3:
        return 'timeline'

    # 9. Stats / data-chart: currency/percent values
    stat_pattern = re.compile(r'^[\$€£]\d[\d,.]*|^\d[\d,.]*[%xX+]')
    stat_lines = sum(1 for l in lines
                     if stat_pattern.match(l) and not re.match(r'^\d+[\.\)]\s', l))
    if stat_lines >= 2:
        return 'data-chart'

    # 10. Cards: 3+ H3 headings or 4+ bullet items
    bullet_count = sum(1 for l in lines if l.startswith('- ') or l.startswith('* '))
    if h3_count >= 3:
        return 'content'
    if bullet_count >= 4:
        return 'content'

    # 11. Key message: very short body (≤50 words, single paragraph-like)
    word_count = len(' '.join(lines).split())
    paragraph_breaks = body_text.count('\n\n')
    if word_count <= 50 and paragraph_breaks <= 1:
        return 'key-message'

    # 12. Default
    return 'content'


def _extract_items(body_text):
    """Extract structured items (bullets, numbered) from body text."""
    items = []
    for line in body_text.strip().split('\n'):
        line = line.strip()
        # Bullet items
        m = re.match(r'^[-*]\s+(.+)$', line)
        if m:
            items.append(m.group(1))
            continue
        # Numbered items
        m = re.match(r'^\d+[\.\)]\s+(.+)$', line)
        if m:
            items.append(m.group(1))
    return items


def _split_into_raw_slides(markdown):
    """Split markdown into raw slide chunks.

    Splits on:
    1. Horizontal rules: a line that is just `---` (3+ dashes)
    2. H2 headings: lines starting with `## `

    For H2 splits, the heading is included in the new chunk.
    """
    lines = markdown.split('\n')
    chunks = []
    current_chunk = []

    for line in lines:
        stripped = line.strip()

        # Horizontal rule: 3+ dashes on a line by themselves
        if re.match(r'^-{3,}\s*$', stripped) and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            continue

        # H2 heading starts a new slide (unless we're at the very beginning)
        if stripped.startswith('## ') and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            continue

        current_chunk.append(line)

    if current_chunk:
        chunks.append('\n'.join(current_chunk))

    return chunks


def _parse_chunk(chunk_text, index, model_sections=None):
    """Parse a raw chunk of markdown into a Slide object."""
    lines = chunk_text.strip().split('\n')
    slide = Slide()

    if index == 0:
        slide.is_title_slide = True
        slide.layout_hint = 'title'

    title_line = None
    body_lines = []

    for line in lines:
        stripped = line.strip()

        # H1 — deck title (usually first slide only)
        if stripped.startswith('# ') and not stripped.startswith('## '):
            slide.title = stripped[2:].strip()
            title_line = stripped
            continue

        # H2 — slide title
        if stripped.startswith('## '):
            slide.title = stripped[3:].strip()
            title_line = stripped
            continue

        # H3 — could be a card heading or sub-section
        if stripped.startswith('### '):
            body_lines.append(line)
            continue

        body_lines.append(line)

    slide.body = '\n'.join(body_lines).strip()

    # For title slide, extract subtitle from first non-empty paragraph
    if slide.is_title_slide and slide.body:
        paragraphs = [p.strip() for p in slide.body.split('\n\n') if p.strip()]
        if paragraphs:
            slide.subtitle = paragraphs[0]

    # Extract items
    slide.items = _extract_items(slide.body)

    # Auto-detect layout if not title slide
    if not slide.is_title_slide:
        slide.layout_hint = _detect_layout_hint(slide.title, slide.body)

    # Parse structured data for specific types
    if slide.layout_hint == 'table' and slide.body:
        slide.table_data = _parse_table_data(slide.body)
    elif slide.layout_hint == 'matrix' and slide.body:
        # Extract 4 quadrants from H3 sections
        quadrants = []
        current_q = None
        for line in slide.body.strip().split('\n'):
            stripped = line.strip()
            if stripped.startswith('### '):
                if current_q:
                    quadrants.append(current_q)
                current_q = {'title': stripped[4:], 'body': ''}
            elif current_q is not None and stripped:
                if current_q['body']:
                    current_q['body'] += ' '
                current_q['body'] += stripped
        if current_q:
            quadrants.append(current_q)
        slide.matrix_quadrants = quadrants[:4]

    # Map section labels from model
    if model_sections and slide.title:
        title_lower = slide.title.lower()
        for section in model_sections:
            if isinstance(section, str):
                if section.lower() in title_lower or title_lower in section.lower():
                    slide.section_label = section
                    break
            elif isinstance(section, dict):
                name = section.get('name', '')
                if name.lower() in title_lower or title_lower in name.lower():
                    slide.section_label = name
                    break

    return slide


def _get_model_sections(model_data):
    """Extract section names from a model YAML structure."""
    if not model_data:
        return []

    sections = []
    # Try common model structures
    if isinstance(model_data, dict):
        # Look for a 'sections' key
        if 'sections' in model_data:
            return model_data['sections']
        # Look for top-level keys that look like sections
        for key, value in model_data.items():
            if key not in ('metadata', 'meta', 'config', 'settings'):
                sections.append(key)
    return sections


def parse_markdown(markdown, model_name=None):
    """Parse markdown content into a list of Slide objects.

    Args:
        markdown: Raw markdown string
        model_name: Optional deliverable model name to load for section mapping

    Returns:
        list[Slide]: Ordered list of slides
    """
    if not markdown or not markdown.strip():
        return []

    model_data = load_model(model_name) if model_name else None
    model_sections = _get_model_sections(model_data)

    raw_chunks = _split_into_raw_slides(markdown)
    slides = []

    for i, chunk in enumerate(raw_chunks):
        if not chunk.strip():
            continue
        slide = _parse_chunk(chunk, i, model_sections)
        slides.append(slide)

    # Last slide defaults to closing if not explicitly typed otherwise
    if len(slides) > 1 and slides[-1].layout_hint == 'content':
        last_title = slides[-1].title.lower() if slides[-1].title else ''
        if any(kw in last_title for kw in ['thank', 'question', 'q&a', 'contact', 'closing']):
            slides[-1].layout_hint = 'closing'

    return slides


def model_to_markdown_template(model_name):
    """Convert a deliverable model to a markdown template with placeholder content.

    Returns a markdown string with H1 title, H2 sections, and placeholder text.
    """
    model_data = load_model(model_name)
    if not model_data:
        return f'# {model_name.replace("-", " ").title()}\n\nEnter your content here.\n'

    lines = []

    # Try to extract a title from the model
    title = model_name.replace('-', ' ').title()
    if isinstance(model_data, dict):
        meta = model_data.get('metadata', model_data.get('meta', {}))
        if isinstance(meta, dict):
            title = meta.get('title', title)

    lines.append(f'# {title}')
    lines.append('')
    lines.append('A brief subtitle or description for this deck.')
    lines.append('')

    # Generate sections from model structure
    sections = _get_model_sections(model_data)
    for section in sections:
        if isinstance(section, str):
            section_name = section.replace('_', ' ').title()
            lines.append(f'## {section_name}')
            lines.append('')
            lines.append(f'Content for {section_name.lower()} goes here.')
            lines.append('')
        elif isinstance(section, dict):
            section_name = section.get('name', 'Section')
            description = section.get('description', f'Content for {section_name.lower()} goes here.')
            lines.append(f'## {section_name}')
            lines.append('')
            lines.append(description)
            lines.append('')

    # If no sections found, create a generic template
    if not sections:
        lines.append('## Overview')
        lines.append('')
        lines.append('Enter overview content here.')
        lines.append('')
        lines.append('## Details')
        lines.append('')
        lines.append('Enter detail content here.')
        lines.append('')

    return '\n'.join(lines)


def list_models():
    """List available deliverable models, grouped by function.

    Returns:
        dict: {'sales': [{'name': 'quote', 'path': '...'}], 'delivery': [...]}
    """
    models = {}

    if not os.path.isdir(MODELS_DIR):
        return models

    for subdir in sorted(os.listdir(MODELS_DIR)):
        subdir_path = os.path.join(MODELS_DIR, subdir)
        if not os.path.isdir(subdir_path):
            continue

        group_models = []
        for fname in sorted(os.listdir(subdir_path)):
            if fname.endswith(('.yaml', '.yml')):
                name = fname.rsplit('.', 1)[0]
                group_models.append({
                    'name': name,
                    'label': name.replace('-', ' ').title(),
                    'group': subdir,
                })
        if group_models:
            models[subdir] = group_models

    return models
