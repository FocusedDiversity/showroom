"""
Authoring Routes — Flask routes for the deck authoring workflow.

Registered as a Blueprint so app.py stays clean.
"""

import json
import base64
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, abort
)
from db import get_db
from storage import get_storage
from authoring.parser import parse_markdown, list_models, model_to_markdown_template
from authoring.theme import get_theme
from authoring.generator import generate_deck
from authoring.variants import generate_variants
from authoring.collage import (
    list_collages, get_collage, upload_collage,
    get_collage_data_uri, generate_collage_recraft,
    save_generated_collage,
)

authoring_bp = Blueprint('authoring', __name__)

AUTHORING_SLUG = '_authoring'


@authoring_bp.route('/admin/author', methods=['GET'])
def author_form():
    """Authoring entry form."""
    models = list_models()
    db = get_db()
    collages = list_collages(db)
    return render_template('admin/author.html', models=models, collages=collages)


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
    """Parse content, generate variants, create session."""
    db = get_db()
    storage = get_storage()

    title = request.form.get('title', 'Untitled Deck')
    markdown_content = request.form.get('markdown_content', '')
    model_name = request.form.get('model_name', '') or None
    theme_name = request.form.get('theme_name', 'synaptiq')
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
           (title, markdown_content, model_name, theme_name, collage_id, status)
           VALUES (%s, %s, %s, %s, %s, 'previewing')
           RETURNING *""",
        (title, markdown_content, model_name, theme_name,
         int(collage_id) if collage_id else None)
    ).fetchone()
    db.commit()
    session_id = session_row['id']

    # Generate variants
    theme = get_theme(theme_name)
    variant_results = generate_variants(
        slides, theme, collage_data_uri=collage_data_uri,
        deck_title=title, num_variants=3
    )

    # Store variants
    for i, variant in enumerate(variant_results):
        storage_path = f'{session_id}/variant_{i}.html'
        storage.save_file(AUTHORING_SLUG, storage_path, variant['html'].encode('utf-8'))

        db.execute(
            """INSERT INTO session_variants
               (session_id, variant_index, html_storage_path, layout_config, color_config)
               VALUES (%s, %s, %s, %s, %s)""",
            (session_id, i, storage_path,
             json.dumps(variant['layout_config']),
             json.dumps(variant['color_config']))
        )
    db.commit()

    return redirect(url_for('authoring.preview_variants', session_id=session_id))


@authoring_bp.route('/admin/author/preview/<int:session_id>')
def preview_variants(session_id):
    """Preview selection page showing 2-3 variants."""
    db = get_db()
    session = db.execute(
        'SELECT * FROM authoring_sessions WHERE id = %s', (session_id,)
    ).fetchone()
    if not session:
        abort(404)

    variants = db.execute(
        'SELECT * FROM session_variants WHERE session_id = %s ORDER BY variant_index',
        (session_id,)
    ).fetchall()

    return render_template('admin/author_preview.html',
                           session=session, variants=variants)


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

    # Deselect all, select chosen
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

    # Count revisions
    rev_count = db.execute(
        'SELECT COUNT(*) as cnt FROM session_feedback WHERE session_id = %s',
        (session_id,)
    ).fetchone()['cnt']

    # Save feedback
    db.execute(
        """INSERT INTO session_feedback
           (session_id, variant_id, feedback_text, revision_number)
           VALUES (%s, %s, %s, %s)""",
        (session_id, variant['id'], feedback_text, rev_count + 1)
    )

    # Regenerate: re-parse and re-generate with the same config
    # For now, regenerate with the same settings (future: interpret feedback)
    slides = parse_markdown(session['markdown_content'], model_name=session['model_name'])
    theme = get_theme(session['theme_name'])

    collage_data_uri = ''
    if session['collage_id']:
        collage = get_collage(db, session['collage_id'])
        if collage:
            collage_data_uri = get_collage_data_uri(storage, collage)

    # psycopg3 auto-deserializes JSONB columns to dicts
    color_config = variant['color_config'] or {}
    layout_config = variant['layout_config'] or {}
    if isinstance(color_config, str):
        color_config = json.loads(color_config)
    if isinstance(layout_config, str):
        layout_config = json.loads(layout_config)

    # Apply layout config to slides
    if layout_config.get('slides'):
        for slide_cfg in layout_config['slides']:
            idx = slide_cfg['index']
            if idx < len(slides):
                slides[idx].layout_hint = slide_cfg['layout']

    html = generate_deck(slides, theme, collage_data_uri=collage_data_uri,
                         deck_title=session['title'])

    # Update stored HTML
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

    # Generate unique slug
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while db.execute('SELECT 1 FROM decks WHERE slug = %s', (slug,)).fetchone():
        slug = f'{base_slug}-{counter}'
        counter += 1

    # Read variant HTML
    html = storage.read_file(AUTHORING_SLUG, variant['html_storage_path'])

    # Create deck (same as manual upload flow)
    deck = db.execute(
        """INSERT INTO decks (title, slug, description)
           VALUES (%s, %s, %s) RETURNING *""",
        (title, slug, description)
    ).fetchone()

    # Store HTML
    storage.save_file(slug, 'index.html', html.encode('utf-8'))

    # Update session status
    db.execute(
        "UPDATE authoring_sessions SET status = 'published', updated_at = NOW() WHERE id = %s",
        (session_id,)
    )
    db.commit()

    flash(f'Deck "{title}" published successfully!', 'success')
    return redirect(url_for('admin_deck_detail', deck_id=deck['id']))


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
