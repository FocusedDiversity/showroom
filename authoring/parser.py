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
    layout_hint: str = 'text'
    section_label: str = ''
    is_title_slide: bool = False
    subtitle: str = ''
    items: list = field(default_factory=list)


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


def _detect_layout_hint(body_text):
    """Auto-detect layout hint from content structure."""
    lines = [l.strip() for l in body_text.strip().split('\n') if l.strip()]

    if not lines:
        return 'text'

    # Timeline: numbered list items (1. 2. 3.) or "Phase/Step/Week" keywords
    # Check before stats since numbered items can look like numbers
    numbered_count = sum(1 for l in lines if re.match(r'^\d+[\.\)]\s', l))
    timeline_keywords = sum(1 for l in lines
                           if re.search(r'\b(phase|step|week|stage|month|day)\b', l, re.I))
    if numbered_count >= 3 or timeline_keywords >= 3:
        return 'timeline'

    # Stats: lines that start with a currency/number/percent (but NOT numbered list items)
    stat_pattern = re.compile(r'^[\$€£]\d[\d,.]*|^\d[\d,.]*[%xX+]')
    stat_lines = sum(1 for l in lines
                     if stat_pattern.match(l) and not re.match(r'^\d+[\.\)]\s', l))
    if stat_lines >= 2:
        return 'stats'

    # Cards: 3+ bullet items or 3+ H3 headings
    bullet_count = sum(1 for l in lines if l.startswith('- ') or l.startswith('* '))
    h3_count = sum(1 for l in lines if l.startswith('### '))
    if h3_count >= 3:
        return 'cards'
    if bullet_count >= 4:
        return 'cards'

    # Split: contains an image reference or blockquote + other content
    has_image = any(re.match(r'!\[', l) for l in lines)
    has_blockquote = any(l.startswith('> ') for l in lines)
    non_special = [l for l in lines if not l.startswith('> ') and not re.match(r'!\[', l)]
    if (has_image or has_blockquote) and len(non_special) >= 2:
        return 'split'

    return 'text'


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
        slide.layout_hint = _detect_layout_hint(slide.body)

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
