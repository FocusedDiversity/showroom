import secrets
import re
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, abort
)
from slugify import slugify
from db import get_db, close_db, init_db
from config import SECRET_KEY, MAX_CONTENT_LENGTH
from storage import get_storage

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

app.teardown_appcontext(close_db)

storage = get_storage()

# Register authoring blueprint
from authoring.routes import authoring_bp
app.register_blueprint(authoring_bp)


# ── Helpers ──────────────────────────────────────────────────────────

def unique_slug(title):
    base = slugify(title)
    slug = base
    db = get_db()
    counter = 1
    while db.execute('SELECT 1 FROM decks WHERE slug = %s', (slug,)).fetchone():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


def inject_base_tag(html_content, base_url):
    """Inject a <base> tag after <head> so relative URLs resolve to our asset route."""
    tag = f'<base href="{base_url}">'
    pattern = re.compile(r'(<head[^>]*>)', re.IGNORECASE)
    if pattern.search(html_content):
        return pattern.sub(r'\1' + tag, html_content, count=1)
    return tag + html_content


def inject_slide_tracking(html_content):
    """Inject a script that posts slide changes to the parent window."""
    tracking_script = '''
<script>
(function() {
  var lastSlide = null;
  // Detect if slides are 0-based or 1-based by checking first slide's data-slide value
  var firstSlide = document.querySelector('.slide[data-slide]');
  var zeroIndexed = firstSlide && parseInt(firstSlide.dataset.slide) === 0;
  function detectSlide() {
    var slide = null;
    // Method 1: Active slide with data-slide attribute
    var active = document.querySelector('.slide.active[data-slide]');
    if (active) {
      slide = parseInt(active.dataset.slide);
      if (zeroIndexed) slide = slide + 1;
    }
    // Method 2: Parse "N / M" from any slide indicator
    if (!slide) {
      var el = document.getElementById('slideNum') || document.getElementById('slideIndicator') || document.querySelector('.slide-indicator');
      if (el) {
        var m = el.textContent.match(/(\\d+)\\s*\\/\\s*(\\d+)/);
        if (m) { slide = parseInt(m[1]); }
      }
    }
    if (typeof slide === 'number' && slide > 0 && slide !== lastSlide) {
      lastSlide = slide;
      var total = document.querySelectorAll('.slide[data-slide]').length || document.querySelectorAll('.slide').length || null;
      window.parent.postMessage({type: 'showroom_slide', slide: slide, total: total}, '*');
    }
  }
  setInterval(detectSlide, 500);
  document.addEventListener('keydown', function() { setTimeout(detectSlide, 100); });
  document.addEventListener('click', function() { setTimeout(detectSlide, 100); });
  setTimeout(detectSlide, 300);
})();
</script>'''
    # Inject before </body> using string replacement (not re.sub, which
    # would interpret backslashes in the JS as regex escapes)
    body_close = re.compile(r'</body>', re.IGNORECASE)
    m = body_close.search(html_content)
    if m:
        return html_content[:m.start()] + tracking_script + html_content[m.start():]
    return html_content + tracking_script


# ── Admin Routes ─────────────────────────────────────────────────────

@app.route('/')
def index():
    if request.host.startswith('showcase.synaptiq.ai'):
        return redirect('/v/kc-w27Yh-Wd1Xeq3i1XsNw')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin')
def admin_dashboard():
    db = get_db()
    decks = db.execute('''
        SELECT d.*,
               COUNT(DISTINCT sl.id) as link_count,
               COUNT(DISTINCT v.id) as view_count
        FROM decks d
        LEFT JOIN share_links sl ON sl.deck_id = d.id
        LEFT JOIN views v ON v.share_link_id = sl.id
        GROUP BY d.id
        ORDER BY d.created_at DESC
    ''').fetchall()
    # Fetch in-progress authoring sessions
    authoring_sessions = db.execute(
        """SELECT * FROM authoring_sessions
           WHERE status IN ('drafting', 'previewing', 'refining')
           ORDER BY updated_at DESC"""
    ).fetchall()

    return render_template('admin/dashboard.html', decks=decks,
                           authoring_sessions=authoring_sessions)


@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    file = request.files.get('file')

    if not title:
        flash('Title is required.', 'error')
        return redirect(url_for('admin_dashboard'))

    if not file or file.filename == '':
        flash('Please select a file to upload.', 'error')
        return redirect(url_for('admin_dashboard'))

    slug = unique_slug(title)
    filename = file.filename.lower()

    try:
        if filename.endswith('.zip'):
            storage.extract_zip(slug, file.read())

            if not storage.file_exists(slug, 'index.html'):
                storage.delete_deck(slug)
                flash('ZIP must contain an index.html file.', 'error')
                return redirect(url_for('admin_dashboard'))

        elif filename.endswith('.html') or filename.endswith('.htm'):
            storage.save_file(slug, 'index.html', file.read())
        else:
            flash('Please upload an HTML file or a ZIP archive.', 'error')
            return redirect(url_for('admin_dashboard'))

    except (ValueError, Exception) as e:
        storage.delete_deck(slug)
        flash(f'Upload failed: {e}', 'error')
        return redirect(url_for('admin_dashboard'))

    # Record assets
    db = get_db()
    row = db.execute(
        'INSERT INTO decks (title, slug, description) VALUES (%s, %s, %s) RETURNING id',
        (title, slug, description)
    ).fetchone()
    deck_id = row['id']

    for rel_path in storage.list_files(slug):
        fname = rel_path.split('/')[-1] if '/' in rel_path else rel_path
        db.execute(
            'INSERT INTO deck_assets (deck_id, filename, filepath) VALUES (%s, %s, %s)',
            (deck_id, fname, rel_path)
        )
    db.commit()

    flash(f'Deck "{title}" uploaded successfully.', 'success')
    return redirect(url_for('admin_deck_detail', deck_id=deck_id))


@app.route('/admin/deck/<int:deck_id>')
def admin_deck_detail(deck_id):
    db = get_db()
    deck = db.execute('SELECT * FROM decks WHERE id = %s', (deck_id,)).fetchone()
    if not deck:
        abort(404)

    share_links = db.execute('''
        SELECT sl.*, COUNT(v.id) as view_count
        FROM share_links sl
        LEFT JOIN views v ON v.share_link_id = sl.id
        WHERE sl.deck_id = %s
        GROUP BY sl.id
        ORDER BY sl.created_at DESC
    ''', (deck_id,)).fetchall()

    return render_template('admin/deck_detail.html', deck=deck, share_links=share_links)


@app.route('/admin/deck/<int:deck_id>/toggle', methods=['POST'])
def admin_deck_toggle(deck_id):
    db = get_db()
    db.execute('UPDATE decks SET is_active = NOT is_active WHERE id = %s', (deck_id,))
    db.commit()
    flash('Deck status updated.', 'success')
    return redirect(url_for('admin_deck_detail', deck_id=deck_id))


@app.route('/admin/deck/<int:deck_id>/delete', methods=['POST'])
def admin_deck_delete(deck_id):
    db = get_db()
    deck = db.execute('SELECT slug FROM decks WHERE id = %s', (deck_id,)).fetchone()
    if deck:
        storage.delete_deck(deck['slug'])
        db.execute('DELETE FROM decks WHERE id = %s', (deck_id,))
        db.commit()
        flash('Deck deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/deck/<int:deck_id>/share', methods=['POST'])
def admin_create_share(deck_id):
    email = request.form.get('email', '').strip().lower()
    if not email:
        flash('Recipient email is required.', 'error')
        return redirect(url_for('admin_deck_detail', deck_id=deck_id))

    db = get_db()
    deck = db.execute('SELECT * FROM decks WHERE id = %s', (deck_id,)).fetchone()
    if not deck:
        abort(404)

    feedback_enabled = request.form.get('feedback_enabled') == 'on'

    token = secrets.token_urlsafe(16)
    db.execute(
        'INSERT INTO share_links (deck_id, recipient_email, token, feedback_enabled) VALUES (%s, %s, %s, %s)',
        (deck_id, email, token, feedback_enabled)
    )
    db.commit()

    share_url = request.host_url.rstrip('/') + url_for('viewer_gate', token=token)
    flash(f'Share link created for {email}: {share_url}', 'success')
    return redirect(url_for('admin_deck_detail', deck_id=deck_id))


@app.route('/admin/share/<int:link_id>/toggle', methods=['POST'])
def admin_share_toggle(link_id):
    db = get_db()
    link = db.execute('SELECT deck_id FROM share_links WHERE id = %s', (link_id,)).fetchone()
    if not link:
        abort(404)
    db.execute('UPDATE share_links SET is_active = NOT is_active WHERE id = %s', (link_id,))
    db.commit()
    flash('Share link updated.', 'success')
    return redirect(url_for('admin_deck_detail', deck_id=link['deck_id']))


@app.route('/admin/deck/<int:deck_id>/analytics')
def admin_analytics(deck_id):
    db = get_db()
    deck = db.execute('SELECT * FROM decks WHERE id = %s', (deck_id,)).fetchone()
    if not deck:
        abort(404)
    return render_template('admin/analytics.html', deck=deck)


@app.route('/admin/api/analytics/<int:deck_id>')
def admin_analytics_api(deck_id):
    db = get_db()
    deck = db.execute('SELECT * FROM decks WHERE id = %s', (deck_id,)).fetchone()
    if not deck:
        return jsonify({'error': 'Not found'}), 404

    # Summary stats
    summary = db.execute('''
        SELECT
            COUNT(DISTINCT v.id) as total_views,
            COUNT(DISTINCT v.viewer_email) as unique_viewers,
            COALESCE(SUM(v.duration_seconds), 0) as total_duration,
            COALESCE(AVG(v.duration_seconds), 0) as avg_duration,
            COUNT(CASE WHEN v.is_forwarded THEN 1 END) as forwarded_views
        FROM views v
        JOIN share_links sl ON sl.id = v.share_link_id
        WHERE sl.deck_id = %s
    ''', (deck_id,)).fetchone()

    # Individual views
    views = db.execute('''
        SELECT v.*, sl.recipient_email as shared_with
        FROM views v
        JOIN share_links sl ON sl.id = v.share_link_id
        WHERE sl.deck_id = %s
        ORDER BY v.viewed_at DESC
    ''', (deck_id,)).fetchall()

    # Views over time (by day)
    daily = db.execute('''
        SELECT DATE(v.viewed_at)::text as day, COUNT(*) as count
        FROM views v
        JOIN share_links sl ON sl.id = v.share_link_id
        WHERE sl.deck_id = %s
        GROUP BY DATE(v.viewed_at)
        ORDER BY day
    ''', (deck_id,)).fetchall()

    # Feedback
    feedback = db.execute('''
        SELECT sf.id, sf.slide_number, sf.comment, sf.created_at,
               v.viewer_email
        FROM slide_feedback sf
        JOIN views v ON v.id = sf.view_id
        JOIN share_links sl ON sl.id = v.share_link_id
        WHERE sl.deck_id = %s
        ORDER BY sf.created_at DESC
    ''', (deck_id,)).fetchall()

    return jsonify({
        'summary': {
            'total_views': summary['total_views'],
            'unique_viewers': summary['unique_viewers'],
            'total_duration': summary['total_duration'],
            'avg_duration': round(float(summary['avg_duration'])),
            'forwarded_views': summary['forwarded_views'] or 0,
        },
        'views': [{
            'viewer_email': v['viewer_email'],
            'shared_with': v['shared_with'],
            'viewed_at': v['viewed_at'].isoformat() if hasattr(v['viewed_at'], 'isoformat') else v['viewed_at'],
            'duration_seconds': v['duration_seconds'],
            'user_agent': v['user_agent'],
            'ip_address': v['ip_address'],
            'is_forwarded': bool(v['is_forwarded']),
            'current_slide': v['current_slide'],
            'total_slides': v['total_slides'],
        } for v in views],
        'daily': [{'day': d['day'], 'count': d['count']} for d in daily],
        'feedback': [{
            'id': f['id'],
            'slide_number': f['slide_number'],
            'viewer_email': f['viewer_email'],
            'comment': f['comment'],
            'created_at': f['created_at'].isoformat() if hasattr(f['created_at'], 'isoformat') else f['created_at'],
        } for f in feedback],
        'feedback_count': len(feedback),
    })


# ── Viewer Routes ────────────────────────────────────────────────────

@app.route('/v/<token>', methods=['GET', 'POST'])
def viewer_gate(token):
    db = get_db()
    link = db.execute('''
        SELECT sl.*, d.title, d.is_active as deck_active
        FROM share_links sl
        JOIN decks d ON d.id = sl.deck_id
        WHERE sl.token = %s
    ''', (token,)).fetchone()

    if not link or not link['is_active'] or not link['deck_active']:
        return render_template('viewer/link_expired.html'), 404

    session_key = f'viewer_email_{token}'

    if session.get(session_key):
        return redirect(url_for('viewer_deck', token=token))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            return render_template('viewer/email_gate.html', token=token, title=link['title'],
                                   error='Please enter your email address.')

        session[session_key] = email

        is_forwarded = email != link['recipient_email']
        db.execute('''
            INSERT INTO views (share_link_id, viewer_email, user_agent, ip_address, referrer, is_forwarded)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            link['id'],
            email,
            request.headers.get('User-Agent', ''),
            request.remote_addr or '',
            request.referrer or '',
            is_forwarded,
        ))
        db.commit()

        return redirect(url_for('viewer_deck', token=token))

    return render_template('viewer/email_gate.html', token=token, title=link['title'])


@app.route('/v/<token>/view')
def viewer_deck(token):
    db = get_db()
    link = db.execute('''
        SELECT sl.*, d.title, d.slug, d.is_active as deck_active
        FROM share_links sl
        JOIN decks d ON d.id = sl.deck_id
        WHERE sl.token = %s
    ''', (token,)).fetchone()

    if not link or not link['is_active'] or not link['deck_active']:
        return render_template('viewer/link_expired.html'), 404

    session_key = f'viewer_email_{token}'
    viewer_email = session.get(session_key)
    if not viewer_email:
        return redirect(url_for('viewer_gate', token=token))

    view = db.execute('''
        SELECT id FROM views
        WHERE share_link_id = %s AND viewer_email = %s
        ORDER BY viewed_at DESC LIMIT 1
    ''', (link['id'], viewer_email)).fetchone()

    view_id = view['id'] if view else None

    return render_template('viewer/deck_view.html',
                           token=token, title=link['title'], view_id=view_id,
                           feedback_enabled=bool(link['feedback_enabled']))


@app.route('/v/<token>/raw')
def viewer_raw(token):
    db = get_db()
    link = db.execute('''
        SELECT sl.*, d.slug, d.is_active as deck_active
        FROM share_links sl
        JOIN decks d ON d.id = sl.deck_id
        WHERE sl.token = %s
    ''', (token,)).fetchone()

    if not link or not link['is_active'] or not link['deck_active']:
        abort(404)

    session_key = f'viewer_email_{token}'
    if not session.get(session_key):
        abort(403)

    if not storage.file_exists(link['slug'], 'index.html'):
        abort(404)

    html = storage.read_file(link['slug'], 'index.html')

    base_url = url_for('viewer_asset', token=token, path='', _external=False)
    html = inject_base_tag(html, base_url)
    html = inject_slide_tracking(html)

    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/v/<token>/asset/<path:path>')
def viewer_asset(token, path):
    db = get_db()
    link = db.execute('''
        SELECT sl.*, d.slug, d.is_active as deck_active
        FROM share_links sl
        JOIN decks d ON d.id = sl.deck_id
        WHERE sl.token = %s
    ''', (token,)).fetchone()

    if not link or not link['is_active'] or not link['deck_active']:
        abort(404)

    return storage.serve_file(link['slug'], path)


# ── Heartbeat API ────────────────────────────────────────────────────

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'ok': False}), 400

    view_id = data.get('view_id')
    duration = data.get('duration')
    current_slide = data.get('current_slide')
    total_slides = data.get('total_slides')

    if not view_id or duration is None:
        return jsonify({'ok': False}), 400

    db = get_db()
    db.execute(
        'UPDATE views SET duration_seconds = %s, current_slide = %s, total_slides = %s WHERE id = %s',
        (int(duration), current_slide, total_slides, int(view_id))
    )
    db.commit()

    return jsonify({'ok': True})


# ── Feedback API ────────────────────────────────────────────────────

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'ok': False, 'error': 'Invalid request'}), 400

    try:
        view_id = data.get('view_id')
        slide_number = data.get('slide_number')
        comment = (data.get('comment') or '').strip()

        if not view_id or not slide_number or not comment:
            return jsonify({'ok': False, 'error': 'Missing required fields'}), 400

        if len(comment) > 1000:
            return jsonify({'ok': False, 'error': 'Comment too long (max 1000 chars)'}), 400

        if slide_number < 1:
            return jsonify({'ok': False, 'error': 'Invalid slide number'}), 400

        db = get_db()
        view = db.execute('SELECT id, viewer_email, share_link_id FROM views WHERE id = %s', (int(view_id),)).fetchone()
        if not view:
            return jsonify({'ok': False, 'error': 'View not found'}), 404

        link = db.execute('SELECT token, feedback_enabled FROM share_links WHERE id = %s', (view['share_link_id'],)).fetchone()
        if not link:
            return jsonify({'ok': False, 'error': 'Not authorized'}), 403

        if not link.get('feedback_enabled', True):
            return jsonify({'ok': False, 'error': 'Feedback is not enabled for this link'}), 403

        session_key = f"viewer_email_{link['token']}"
        viewer_email = session.get(session_key)
        if not viewer_email or viewer_email != view['viewer_email']:
            return jsonify({'ok': False, 'error': 'Not authorized'}), 403

        row = db.execute(
            'INSERT INTO slide_feedback (view_id, slide_number, comment) VALUES (%s, %s, %s) RETURNING id',
            (int(view_id), int(slide_number), comment)
        ).fetchone()
        db.commit()

        return jsonify({'ok': True, 'feedback_id': row['id']})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    view_id = request.args.get('view_id', type=int)
    if not view_id:
        return jsonify({'ok': False, 'error': 'Missing view_id'}), 400

    db = get_db()
    view = db.execute('SELECT id, viewer_email, share_link_id FROM views WHERE id = %s', (view_id,)).fetchone()
    if not view:
        return jsonify({'ok': False, 'error': 'View not found'}), 404

    # Validate session
    link = db.execute('SELECT token FROM share_links WHERE id = %s', (view['share_link_id'],)).fetchone()
    if not link:
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403

    session_key = f"viewer_email_{link['token']}"
    viewer_email = session.get(session_key)
    if not viewer_email or viewer_email != view['viewer_email']:
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403

    feedback = db.execute(
        'SELECT id, slide_number, comment, created_at FROM slide_feedback WHERE view_id = %s ORDER BY created_at ASC',
        (view_id,)
    ).fetchall()

    return jsonify({
        'ok': True,
        'feedback': [{
            'id': f['id'],
            'slide_number': f['slide_number'],
            'comment': f['comment'],
            'created_at': f['created_at'].isoformat() if hasattr(f['created_at'], 'isoformat') else f['created_at'],
        } for f in feedback]
    })


def obfuscate_email(email):
    """Obfuscate email: s***@acme.com"""
    if not email or '@' not in email:
        return '***'
    local, domain = email.split('@', 1)
    return local[0] + '***@' + domain if local else '***@' + domain


@app.route('/api/feedback/all', methods=['GET'])
def get_all_feedback():
    view_id = request.args.get('view_id', type=int)
    if not view_id:
        return jsonify({'ok': False, 'error': 'Missing view_id'}), 400

    db = get_db()
    view = db.execute('SELECT id, viewer_email, share_link_id FROM views WHERE id = %s', (view_id,)).fetchone()
    if not view:
        return jsonify({'ok': False, 'error': 'View not found'}), 404

    # Validate session
    link = db.execute('SELECT token, deck_id, feedback_enabled FROM share_links WHERE id = %s', (view['share_link_id'],)).fetchone()
    if not link:
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403

    if not link['feedback_enabled']:
        return jsonify({'ok': False, 'error': 'Feedback is not enabled for this link'}), 403

    session_key = f"viewer_email_{link['token']}"
    viewer_email = session.get(session_key)
    if not viewer_email:
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403

    # Get ALL feedback for this deck
    feedback = db.execute('''
        SELECT sf.id, sf.slide_number, sf.comment, sf.created_at,
               v.viewer_email
        FROM slide_feedback sf
        JOIN views v ON v.id = sf.view_id
        JOIN share_links sl ON sl.id = v.share_link_id
        WHERE sl.deck_id = %s
        ORDER BY sf.created_at ASC
    ''', (link['deck_id'],)).fetchall()

    return jsonify({
        'ok': True,
        'feedback': [{
            'id': f['id'],
            'slide_number': f['slide_number'],
            'comment': f['comment'],
            'viewer_email': 'You' if f['viewer_email'] == viewer_email else obfuscate_email(f['viewer_email']),
            'is_own': f['viewer_email'] == viewer_email,
            'created_at': f['created_at'].isoformat() if hasattr(f['created_at'], 'isoformat') else f['created_at'],
        } for f in feedback],
    })


# ── Init DB on import (for gunicorn) ─────────────────────────────────

init_db(app)

if __name__ == '__main__':
    app.run(debug=True, port=5111)
