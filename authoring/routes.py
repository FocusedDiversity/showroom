"""
Authoring Routes — Flask routes for the deck authoring workflow.

Registered as a Blueprint so app.py stays clean.
"""

import json
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, abort
)
from db import get_db
from storage import get_storage
from authoring.parser import parse_markdown, list_models, model_to_markdown_template
from authoring.palettes import list_palettes, get_palette
from authoring.fonts import list_font_pairings, get_font_pairing
from authoring.layouts import list_layouts, get_layout
from authoring.generator import generate_deck
from authoring.collage import (
    list_collages, get_collage, upload_collage,
    get_collage_data_uri, generate_collage_recraft,
    save_generated_collage,
)

authoring_bp = Blueprint('authoring', __name__)

AUTHORING_SLUG = '_authoring'


@authoring_bp.route('/admin/author', methods=['GET'])
def author_form():
    """Authoring entry form with palette, font, and layout collection selectors."""
    models = list_models()
    db = get_db()
    collages = list_collages(db)
    palettes = list_palettes(db)
    font_pairings = list_font_pairings(db)
    layouts = list_layouts(db)
    return render_template('admin/author.html',
                           models=models, collages=collages,
                           palettes=palettes, font_pairings=font_pairings,
                           layouts=layouts)


@authoring_bp.route('/admin/author/model-template', methods=['GET'])
def get_model_template():
    """Return markdown template for a given model (AJAX)."""
    model_name = request.args.get('model', '')
    if not model_name:
        return jsonify({'template': ''})
    template = model_to_markdown_template(model_name)
    return jsonify({'template': template})


@authoring_bp.route('/admin/author', methods=['POST'])
def author_generate():
    """Parse content, generate a single deck with selected palette + font + layout."""
    db = get_db()
    storage = get_storage()

    title = request.form.get('title', 'Untitled Deck')
    markdown_content = request.form.get('markdown_content', '')
    model_name = request.form.get('model_name', '') or None
    palette_slug = request.form.get('palette_slug', 'arctic-breeze')
    font_slug = request.form.get('font_slug', 'classic-serif')
    layout_slug = request.form.get('layout_slug', 'editorial')
    collage_id = request.form.get('collage_id', '') or None

    if not markdown_content.strip():
        flash('Please enter some content.', 'error')
        return redirect(url_for('authoring.author_form'))

    # Parse slides
    slides = parse_markdown(markdown_content, model_name=model_name)
    if not slides:
        flash('Could not parse any slides from the content.', 'error')
        return redirect(url_for('authoring.author_form'))

    # Use title from first slide if not provided
    if title == 'Untitled Deck' and slides[0].title:
        title = slides[0].title

    # Get collage data URI
    collage_data_uri = ''
    if collage_id:
        collage = get_collage(db, int(collage_id))
        if collage:
            collage_data_uri = get_collage_data_uri(storage, collage)

    # Create session
    session_row = db.execute(
        """INSERT INTO authoring_sessions
           (title, markdown_content, model_name, theme_name, palette_slug, font_slug, layout_slug, collage_id, status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'previewing')
           RETURNING *""",
        (title, markdown_content, model_name, 'synaptiq',
         palette_slug, font_slug, layout_slug,
         int(collage_id) if collage_id else None)
    ).fetchone()
    db.commit()
    session_id = session_row['id']

    # Generate single deck
    palette = get_palette(palette_slug, db)
    font_pairing = get_font_pairing(font_slug, db)
    layout = get_layout(layout_slug, db)
    html = generate_deck(
        slides, palette, font_pairing, layout,
        collage_data_uri=collage_data_uri,
        deck_title=title,
    )

    # Store as single variant
    storage_path = f'{session_id}/variant_0.html'
    storage.save_file(AUTHORING_SLUG, storage_path, html.encode('utf-8'))

    layout_config = {
        'slides': [{'index': j, 'layout': s.layout_hint} for j, s in enumerate(slides)]
    }
    color_config = {
        'palette': palette_slug,
        'font': font_slug,
        'layout': layout_slug,
    }

    db.execute(
        """INSERT INTO session_variants
           (session_id, variant_index, html_storage_path, layout_config, color_config, selected)
           VALUES (%s, %s, %s, %s, %s, TRUE)""",
        (session_id, 0, storage_path,
         json.dumps(layout_config),
         json.dumps(color_config))
    )
    db.commit()

    return redirect(url_for('authoring.preview_variants', session_id=session_id))


@authoring_bp.route('/admin/author/preview/<int:session_id>')
def preview_variants(session_id):
    """Preview the generated deck."""
    db = get_db()
    session = db.execute(
        'SELECT * FROM authoring_sessions WHERE id = %s', (session_id,)
    ).fetchone()
    if not session:
        abort(404)

    variant = db.execute(
        'SELECT * FROM session_variants WHERE session_id = %s AND selected = TRUE',
        (session_id,)
    ).fetchone()
    if not variant:
        variant = db.execute(
            'SELECT * FROM session_variants WHERE session_id = %s ORDER BY variant_index LIMIT 1',
            (session_id,)
        ).fetchone()

    if not variant:
        abort(404)

    palette = get_palette(session.get('palette_slug', 'arctic-breeze'), db)
    font_pairing = get_font_pairing(session.get('font_slug', 'classic-serif'), db)
    layout = get_layout(session.get('layout_slug', 'editorial'), db)

    return render_template('admin/author_preview.html',
                           session=session, variant=variant,
                           palette_name=palette.name,
                           font_name=font_pairing.name,
                           layout_name=layout.name)


@authoring_bp.route('/admin/author/preview/<int:session_id>/variant/<int:variant_id>')
def view_variant(session_id, variant_id):
    """Serve a variant HTML file for full preview."""
    db = get_db()
    storage = get_storage()

    variant = db.execute(
        'SELECT * FROM session_variants WHERE id = %s AND session_id = %s',
        (variant_id, session_id)
    ).fetchone()
    if not variant:
        abort(404)

    html = storage.read_file(AUTHORING_SLUG, variant['html_storage_path'])
    return html


@authoring_bp.route('/admin/author/preview/<int:session_id>/select', methods=['POST'])
def select_variant(session_id):
    """Select a variant and redirect to refinement."""
    db = get_db()
    variant_id = request.form.get('variant_id')
    if not variant_id:
        abort(400)

    db.execute(
        'UPDATE session_variants SET selected = FALSE WHERE session_id = %s',
        (session_id,)
    )
    db.execute(
        'UPDATE session_variants SET selected = TRUE WHERE id = %s AND session_id = %s',
        (int(variant_id), session_id)
    )
    db.execute(
        "UPDATE authoring_sessions SET status = 'refining', updated_at = NOW() WHERE id = %s",
        (session_id,)
    )
    db.commit()

    return redirect(url_for('authoring.refine_view', session_id=session_id))


@authoring_bp.route('/admin/author/refine/<int:session_id>')
def refine_view(session_id):
    """Refinement view with feedback loop."""
    db = get_db()
    session = db.execute(
        'SELECT * FROM authoring_sessions WHERE id = %s', (session_id,)
    ).fetchone()
    if not session:
        abort(404)

    variant = db.execute(
        'SELECT * FROM session_variants WHERE session_id = %s AND selected = TRUE',
        (session_id,)
    ).fetchone()
    if not variant:
        flash('Please select a variant first.', 'error')
        return redirect(url_for('authoring.preview_variants', session_id=session_id))

    feedback_history = db.execute(
        """SELECT * FROM session_feedback
           WHERE session_id = %s ORDER BY revision_number""",
        (session_id,)
    ).fetchall()

    return render_template('admin/author_refine.html',
                           session=session, variant=variant,
                           feedback_history=feedback_history)


@authoring_bp.route('/admin/author/refine/<int:session_id>', methods=['POST'])
def apply_feedback(session_id):
    """Apply feedback to regenerate the selected variant."""
    db = get_db()
    storage = get_storage()

    feedback_text = request.form.get('feedback_text', '')
    if not feedback_text.strip():
        flash('Please enter some feedback.', 'error')
        return redirect(url_for('authoring.refine_view', session_id=session_id))

    session = db.execute(
        'SELECT * FROM authoring_sessions WHERE id = %s', (session_id,)
    ).fetchone()
    variant = db.execute(
        'SELECT * FROM session_variants WHERE session_id = %s AND selected = TRUE',
        (session_id,)
    ).fetchone()
    if not session or not variant:
        abort(404)

    rev_count = db.execute(
        'SELECT COUNT(*) as cnt FROM session_feedback WHERE session_id = %s',
        (session_id,)
    ).fetchone()['cnt']

    db.execute(
        """INSERT INTO session_feedback
           (session_id, variant_id, feedback_text, revision_number)
           VALUES (%s, %s, %s, %s)""",
        (session_id, variant['id'], feedback_text, rev_count + 1)
    )

    slides = parse_markdown(session['markdown_content'], model_name=session['model_name'])

    palette = get_palette(session.get('palette_slug', 'arctic-breeze'), db)
    font_pairing = get_font_pairing(session.get('font_slug', 'classic-serif'), db)
    layout = get_layout(session.get('layout_slug', 'editorial'), db)

    collage_data_uri = ''
    if session['collage_id']:
        collage = get_collage(db, session['collage_id'])
        if collage:
            collage_data_uri = get_collage_data_uri(storage, collage)

    layout_config = variant['layout_config'] or {}
    if isinstance(layout_config, str):
        layout_config = json.loads(layout_config)
    if layout_config.get('slides'):
        for slide_cfg in layout_config['slides']:
            idx = slide_cfg['index']
            if idx < len(slides):
                slides[idx].layout_hint = slide_cfg['layout']

    html = generate_deck(slides, palette, font_pairing, layout,
                         collage_data_uri=collage_data_uri,
                         deck_title=session['title'])

    storage.save_file(AUTHORING_SLUG, variant['html_storage_path'],
                      html.encode('utf-8'))

    db.execute(
        'UPDATE authoring_sessions SET updated_at = NOW() WHERE id = %s',
        (session_id,)
    )
    db.commit()

    flash(f'Revision {rev_count + 1} applied.', 'success')
    return redirect(url_for('authoring.refine_view', session_id=session_id))


@authoring_bp.route('/admin/author/refine/<int:session_id>/publish', methods=['POST'])
def publish_deck(session_id):
    """Publish the selected variant to Showroom as a new deck."""
    from slugify import slugify
    db = get_db()
    storage = get_storage()

    session = db.execute(
        'SELECT * FROM authoring_sessions WHERE id = %s', (session_id,)
    ).fetchone()
    variant = db.execute(
        'SELECT * FROM session_variants WHERE session_id = %s AND selected = TRUE',
        (session_id,)
    ).fetchone()
    if not session or not variant:
        abort(404)

    title = request.form.get('title', session['title'])
    description = request.form.get('description', '')

    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while db.execute('SELECT 1 FROM decks WHERE slug = %s', (slug,)).fetchone():
        slug = f'{base_slug}-{counter}'
        counter += 1

    html = storage.read_file(AUTHORING_SLUG, variant['html_storage_path'])

    deck = db.execute(
        """INSERT INTO decks (title, slug, description)
           VALUES (%s, %s, %s) RETURNING *""",
        (title, slug, description)
    ).fetchone()

    storage.save_file(slug, 'index.html', html.encode('utf-8'))

    db.execute(
        "UPDATE authoring_sessions SET status = 'published', updated_at = NOW() WHERE id = %s",
        (session_id,)
    )
    db.commit()

    flash(f'Deck "{title}" published successfully!', 'success')
    return redirect(url_for('admin_deck_detail', deck_id=deck['id']))


# ── PPTX Import ──────────────────────────────────────────────────────

@authoring_bp.route('/admin/author/import', methods=['GET', 'POST'])
def pptx_import():
    """Upload a PPTX and preview extracted design elements."""
    if request.method == 'GET':
        return render_template('admin/author_import.html', extraction=None)

    if 'pptx_file' not in request.files:
        flash('Please select a .pptx file.', 'error')
        return redirect(url_for('authoring.pptx_import'))

    file = request.files['pptx_file']
    if not file.filename or not file.filename.lower().endswith('.pptx'):
        flash('Please upload a .pptx file.', 'error')
        return redirect(url_for('authoring.pptx_import'))

    import tempfile
    import os
    from authoring.pptx_extract import extract_all

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pptx')
    try:
        file.save(tmp.name)
        tmp.close()
        result = extract_all(tmp.name)
    finally:
        os.unlink(tmp.name)

    extraction = {
        'colors': result['colors'],
        'colors_json': json.dumps(result['colors']),
        'fonts': result['fonts'],
        'fonts_json': json.dumps({
            'title_font': result['fonts']['title_font'],
            'content_font': result['fonts']['content_font'],
            'title_google': result['fonts']['title_google'],
            'content_google': result['fonts']['content_google'],
        }),
        'style': result['style'],
        'style_json': json.dumps(result['style']),
        'base_layout': result['base_layout'],
        'image_count': len(result['images']),
        'source_filename': file.filename,
    }

    return render_template('admin/author_import.html', extraction=extraction)


@authoring_bp.route('/admin/author/import/save', methods=['POST'])
def pptx_import_save():
    """Save the extracted palette, font pairing, and layout collection to the database."""
    from slugify import slugify
    db = get_db()

    palette_name = request.form.get('palette_name', '').strip()
    font_name = request.form.get('font_name', '').strip()
    layout_name = request.form.get('layout_name', '').strip()
    colors_json = request.form.get('colors_json', '{}')
    fonts_json = request.form.get('fonts_json', '{}')
    style_json = request.form.get('style_json', '{}')
    base_layout = request.form.get('base_layout', 'editorial')
    source_filename = request.form.get('source_filename', '')

    if not palette_name or not font_name or not layout_name:
        flash('Please provide names for the palette, font pairing, and layout collection.', 'error')
        return redirect(url_for('authoring.pptx_import'))

    colors = json.loads(colors_json)
    fonts = json.loads(fonts_json)
    style = json.loads(style_json)

    # Generate unique slugs
    palette_slug = slugify(palette_name)
    font_slug = slugify(font_name)
    layout_slug = slugify(layout_name)

    counter = 1
    base_slug = palette_slug
    while db.execute('SELECT 1 FROM custom_palettes WHERE slug = %s', (palette_slug,)).fetchone():
        palette_slug = f'{base_slug}-{counter}'
        counter += 1

    counter = 1
    base_slug = font_slug
    while db.execute('SELECT 1 FROM custom_font_pairings WHERE slug = %s', (font_slug,)).fetchone():
        font_slug = f'{base_slug}-{counter}'
        counter += 1

    counter = 1
    base_slug = layout_slug
    while db.execute('SELECT 1 FROM custom_layouts WHERE slug = %s', (layout_slug,)).fetchone():
        layout_slug = f'{base_slug}-{counter}'
        counter += 1

    title_google = fonts.get('title_google', {})
    content_google = fonts.get('content_google', {})
    font_imports_parts = []
    if title_google.get('import'):
        font_imports_parts.append(f"family={title_google['import']}")
    if content_google.get('import') and content_google['import'] != title_google.get('import'):
        font_imports_parts.append(f"family={content_google['import']}")
    font_imports_url = 'https://fonts.googleapis.com/css2?' + '&'.join(font_imports_parts) + '&display=swap' if font_imports_parts else ''

    # Insert palette
    db.execute(
        """INSERT INTO custom_palettes (name, slug, description, palette_data, source, source_filename)
           VALUES (%s, %s, %s, %s, 'pptx', %s)""",
        (palette_name, palette_slug,
         f'Imported from {source_filename}',
         json.dumps(colors), source_filename)
    )

    # Insert font pairing
    font_data = {
        'font_title': title_google.get('family', "'Quicksand', sans-serif"),
        'font_content': content_google.get('family', "'Quicksand', sans-serif"),
        'font_imports': font_imports_url,
    }
    db.execute(
        """INSERT INTO custom_font_pairings (name, slug, description, font_data, source, source_filename)
           VALUES (%s, %s, %s, %s, 'pptx', %s)""",
        (font_name, font_slug,
         f'Imported from {source_filename}',
         json.dumps(font_data), source_filename)
    )

    # Insert layout collection (no font fields)
    layout_data = {
        'style_metadata': style,
    }
    db.execute(
        """INSERT INTO custom_layouts (name, slug, description, layout_data, base_layout_slug, source, source_filename)
           VALUES (%s, %s, %s, %s, %s, 'pptx', %s)""",
        (layout_name, layout_slug,
         f'Imported from {source_filename}',
         json.dumps(layout_data), base_layout, source_filename)
    )

    db.commit()

    flash(f'Palette "{palette_name}", font "{font_name}", and layout "{layout_name}" saved!', 'success')
    return redirect(url_for('authoring.author_form',
                            palette=palette_slug, font=font_slug, layout=layout_slug))


# ── Layout Collection Preview ────────────────────────────────────────

@authoring_bp.route('/admin/author/layouts/<slug>/preview')
def layout_preview(slug):
    """Render a grid of 6 sample slides for a layout collection."""
    db = get_db()
    palette_slug = request.args.get('palette', 'arctic-breeze')
    font_slug = request.args.get('font', 'classic-serif')

    palette = get_palette(palette_slug, db)
    font_pairing = get_font_pairing(font_slug, db)
    layout = get_layout(slug, db)

    # Sample markdown covering 6 key slide types
    sample_md = """# Sample Presentation
A preview of this layout collection.

---

## Overview
This is a content slide with body text demonstrating how paragraphs, lists, and other elements look in this layout.

- First bullet point with supporting detail
- Second bullet point with more context
- Third point tying it all together

---

## Before vs After

### Before
Manual processes, inconsistent branding, slow turnaround times for every deck.

### After
Automated generation, brand-compliant output, minutes instead of hours.

---

## Key Metrics

$2.5M revenue impact
95% client satisfaction
3x faster delivery

---

## Implementation Plan

1. Phase 1: Discovery and setup
2. Phase 2: Design and build
3. Phase 3: Testing and launch

---

## Thank You
Questions? Reach out anytime.
"""
    slides = parse_markdown(sample_md)
    html = generate_deck(slides, palette, font_pairing, layout, deck_title=f'{layout.name} Preview')
    return html


# ── Palette, Font & Layout APIs ──────────────────────────────────────

@authoring_bp.route('/admin/author/palettes')
def palettes_list():
    """JSON list of available palettes."""
    db = get_db()
    palettes = list_palettes(db)
    return jsonify([{
        'slug': p.slug,
        'name': p.name,
        'description': p.description,
        'colors': {
            'background_dark': p.background_dark,
            'background_light': p.background_light,
            'accent_primary': p.accent_primary,
            'accent_secondary': p.accent_secondary,
            'accent_tertiary': p.accent_tertiary,
        }
    } for p in palettes])


@authoring_bp.route('/admin/author/fonts')
def fonts_list():
    """JSON list of available font pairings."""
    db = get_db()
    fonts = list_font_pairings(db)
    return jsonify([{
        'slug': f.slug,
        'name': f.name,
        'description': f.description,
        'font_title': f.font_title,
        'font_content': f.font_content,
    } for f in fonts])


@authoring_bp.route('/admin/author/layouts')
def layouts_list():
    """JSON list of available layout collections."""
    db = get_db()
    layouts = list_layouts(db)
    return jsonify([{
        'slug': l.slug,
        'name': l.name,
        'description': l.description,
    } for l in layouts])


# ── Collage API routes ────────────────────────────────────────────────

@authoring_bp.route('/admin/author/collages')
def collages_list():
    """JSON list of collages."""
    db = get_db()
    collages = list_collages(db)
    return jsonify([{
        'id': c['id'],
        'name': c['name'],
        'tags': c['tags'],
        'source': c['source'],
    } for c in collages])


@authoring_bp.route('/admin/author/collages/upload', methods=['POST'])
def collages_upload():
    """Upload a new collage image."""
    db = get_db()
    storage = get_storage()

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No filename'}), 400

    name = request.form.get('name', file.filename)
    tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
    tags = [t.strip() for t in tags if t.strip()]

    try:
        collage = upload_collage(db, storage, name, file.read(), file.filename, tags)
        return jsonify({'id': collage['id'], 'name': collage['name']})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@authoring_bp.route('/admin/author/collages/generate', methods=['POST'])
def collages_generate():
    """Generate collage via Recraft.ai."""
    data = request.get_json() or {}
    prompt = data.get('prompt', '')
    style = data.get('style', 'digital_illustration')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        results = generate_collage_recraft(prompt, style)
        return jsonify({'images': results})
    except (ValueError, RuntimeError) as e:
        return jsonify({'error': str(e)}), 500
