"""Playwright E2E tests for the feedback toggle feature.

Verifies that admins can create share links with feedback enabled or
disabled, and that viewers see (or don't see) the feedback UI accordingly.
Also verifies that the feedback API rejects requests from disabled links.

Run with:
    pytest tests/test_e2e_feedback_toggle.py --headed --browser chromium \
        --html=tests/reports/feedback_toggle_report.html --self-contained-html

Videos are recorded as MP4 to tests/videos/
"""
import os
import secrets
import pytest
import psycopg
from psycopg.rows import dict_row
from playwright.sync_api import Page, expect

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://showroom:showroom@localhost:5432/showroom')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5111')


SLIDE_HTML = '''<!DOCTYPE html>
<html>
<head><title>Toggle Test Deck</title>
<style>
.slide { display: none; padding: 60px; font-family: sans-serif; min-height: 80vh; }
.slide.active { display: block; }
.slide h1 { font-size: 36px; margin-bottom: 20px; }
.slide p { font-size: 18px; color: #555; }
.slide-indicator { position: fixed; bottom: 20px; right: 20px; font-size: 14px; color: #999; }
nav { position: fixed; bottom: 20px; left: 20px; }
nav button { padding: 8px 16px; margin-right: 8px; cursor: pointer; font-size: 14px; }
</style>
</head>
<body>
<div class="slide active" data-slide="1">
  <h1>Slide 1: Welcome</h1>
  <p>Toggle test deck slide 1.</p>
</div>
<div class="slide" data-slide="2">
  <h1>Slide 2: Content</h1>
  <p>Toggle test deck slide 2.</p>
</div>
<div class="slide-indicator">1 / 2</div>
<nav>
  <button onclick="go(-1)">Prev</button>
  <button onclick="go(1)">Next</button>
</nav>
<script>
var current = 1, total = 2;
function go(dir) {
  var next = current + dir;
  if (next < 1 || next > total) return;
  document.querySelector('.slide[data-slide="'+current+'"]').classList.remove('active');
  current = next;
  document.querySelector('.slide[data-slide="'+current+'"]').classList.add('active');
  document.querySelector('.slide-indicator').textContent = current + ' / ' + total;
}
</script>
</body>
</html>'''


@pytest.fixture(scope="session")
def _toggle_test_deck():
    """Create a deck with two share links: one feedback-enabled, one disabled."""
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    cur = conn.cursor()

    uid = secrets.token_hex(4)
    slug = f'e2e-toggle-{uid}'
    token_on = f'toggle-on-{uid}'
    token_off = f'toggle-off-{uid}'
    email_on = f'fb-on-{uid}@test.com'
    email_off = f'fb-off-{uid}@test.com'

    cur.execute("DELETE FROM decks WHERE slug = %s", (slug,))
    conn.commit()

    cur.execute(
        "INSERT INTO decks (title, slug, description, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
        ('Feedback Toggle Test Deck', slug, 'For toggle E2E tests', True)
    )
    deck_id = cur.fetchone()['id']

    # Feedback-enabled link
    cur.execute(
        "INSERT INTO share_links (deck_id, recipient_email, token, is_active, feedback_enabled) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (deck_id, email_on, token_on, True, True)
    )
    link_on_id = cur.fetchone()['id']

    # Feedback-disabled link
    cur.execute(
        "INSERT INTO share_links (deck_id, recipient_email, token, is_active, feedback_enabled) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (deck_id, email_off, token_off, True, False)
    )
    link_off_id = cur.fetchone()['id']

    conn.commit()

    from storage import get_storage
    storage = get_storage()
    storage.save_file(slug, 'index.html', SLIDE_HTML.encode('utf-8'))

    yield {
        'deck_id': deck_id,
        'slug': slug,
        'link_on_id': link_on_id,
        'link_off_id': link_off_id,
        'token_on': token_on,
        'token_off': token_off,
        'email_on': email_on,
        'email_off': email_off,
    }

    cur.execute("DELETE FROM decks WHERE id = %s", (deck_id,))
    conn.commit()
    try:
        storage.delete_deck(slug)
    except Exception:
        pass
    conn.close()


@pytest.fixture
def context(browser, _toggle_test_deck):
    """Browser context with MP4 video recording."""
    video_dir = os.path.join(os.path.dirname(__file__), 'videos')
    os.makedirs(video_dir, exist_ok=True)

    ctx = browser.new_context(
        record_video_dir=video_dir,
        record_video_size={"width": 1280, "height": 720},
        viewport={"width": 1280, "height": 720},
    )
    yield ctx
    ctx.close()


@pytest.fixture
def page(context):
    p = context.new_page()
    yield p
    p.close()


@pytest.fixture
def test_data(_toggle_test_deck):
    return _toggle_test_deck


def _pass_email_gate(page: Page, token: str, email: str):
    """Navigate to viewer and pass the email gate."""
    page.goto(f'{BASE_URL}/v/{token}')
    page.wait_for_selector('input[type="email"], input[name="email"], .input-large')
    email_input = page.locator('input[type="email"], input[name="email"], .input-large')
    email_input.fill(email)
    page.locator('button[type="submit"], .btn-primary').click()
    # Wait for the deck viewer to load (iframe present)
    page.wait_for_selector('#deck-frame', timeout=10000)


# ─────────────────────────────────────────────────────────────────────
# Admin: Creating links with and without feedback
# ─────────────────────────────────────────────────────────────────────

class TestAdminFeedbackToggleUI:
    """Admin deck detail page shows the feedback checkbox and badges."""

    def test_share_form_has_feedback_checkbox(self, page: Page, test_data):
        """The share link form should have a 'Feedback' checkbox, checked by default."""
        page.goto(f'{BASE_URL}/admin/deck/{test_data["deck_id"]}')
        page.wait_for_selector('input[name="feedback_enabled"]', timeout=5000)

        checkbox = page.locator('input[name="feedback_enabled"]')
        expect(checkbox).to_be_visible()
        expect(checkbox).to_be_checked()

    def test_create_link_with_feedback_shows_on_badge(self, page: Page, test_data):
        """Creating a link with the checkbox checked shows 'On' feedback badge."""
        page.goto(f'{BASE_URL}/admin/deck/{test_data["deck_id"]}')
        page.wait_for_selector('input[name="email"]', timeout=5000)

        uid = secrets.token_hex(3)
        page.locator('input[name="email"]').fill(f'on-test-{uid}@example.com')
        # Checkbox is checked by default, just submit
        page.locator('button:has-text("Create Link")').click()

        # Wait for redirect back to deck detail
        page.wait_for_selector('.data-table', timeout=5000)

        # Find the row for the new link
        row = page.locator('tr', has_text=f'on-test-{uid}@example.com')
        expect(row).to_be_visible()

        # Should have "On" badge in the Feedback column
        feedback_badge = row.locator('.badge', has_text='On')
        expect(feedback_badge).to_be_visible()

    def test_create_link_without_feedback_shows_off_badge(self, page: Page, test_data):
        """Creating a link with the checkbox unchecked shows 'Off' feedback badge."""
        page.goto(f'{BASE_URL}/admin/deck/{test_data["deck_id"]}')
        page.wait_for_selector('input[name="email"]', timeout=5000)

        uid = secrets.token_hex(3)
        page.locator('input[name="email"]').fill(f'off-test-{uid}@example.com')

        # Uncheck the feedback checkbox
        checkbox = page.locator('input[name="feedback_enabled"]')
        checkbox.uncheck()
        expect(checkbox).not_to_be_checked()

        page.locator('button:has-text("Create Link")').click()
        page.wait_for_selector('.data-table', timeout=5000)

        row = page.locator('tr', has_text=f'off-test-{uid}@example.com')
        expect(row).to_be_visible()

        # Should have "Off" badge
        feedback_badge = row.locator('.badge', has_text='Off')
        expect(feedback_badge).to_be_visible()

    def test_existing_links_show_correct_badges(self, page: Page, test_data):
        """Pre-seeded links should show correct On/Off badges."""
        page.goto(f'{BASE_URL}/admin/deck/{test_data["deck_id"]}')
        page.wait_for_selector('.data-table', timeout=5000)

        # Feedback-enabled link row
        on_row = page.locator('tr', has_text=test_data['email_on'])
        expect(on_row).to_be_visible()
        expect(on_row.locator('.badge', has_text='On')).to_be_visible()

        # Feedback-disabled link row
        off_row = page.locator('tr', has_text=test_data['email_off'])
        expect(off_row).to_be_visible()
        expect(off_row.locator('.badge', has_text='Off')).to_be_visible()

    def test_table_has_feedback_column_header(self, page: Page, test_data):
        """The share links table should have a 'Feedback' column header."""
        page.goto(f'{BASE_URL}/admin/deck/{test_data["deck_id"]}')
        page.wait_for_selector('.data-table', timeout=5000)

        header = page.locator('.data-table th', has_text='Feedback')
        expect(header).to_be_visible()


# ─────────────────────────────────────────────────────────────────────
# Viewer: Feedback-enabled link
# ─────────────────────────────────────────────────────────────────────

class TestViewerFeedbackEnabled:
    """Viewer accessing a feedback-enabled link should see the full feedback UI."""

    def test_feedback_button_visible(self, page: Page, test_data):
        """The Feedback toggle button should be visible in the topbar."""
        _pass_email_gate(page, test_data['token_on'], test_data['email_on'])

        btn = page.locator('#feedback-toggle')
        expect(btn).to_be_visible()
        expect(btn).to_contain_text('Feedback')

    def test_feedback_panel_opens(self, page: Page, test_data):
        """Clicking the Feedback button should open the feedback panel."""
        _pass_email_gate(page, test_data['token_on'], test_data['email_on'])

        page.locator('#feedback-toggle').click()
        panel = page.locator('#feedback-panel')
        expect(panel).to_be_visible()
        expect(page.locator('#feedback-input')).to_be_visible()
        expect(page.locator('#feedback-send')).to_be_visible()

    def test_can_submit_feedback(self, page: Page, test_data):
        """Viewer should be able to submit feedback and see confirmation."""
        _pass_email_gate(page, test_data['token_on'], test_data['email_on'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()
        page.locator('#feedback-input').fill('Feedback toggle enabled test!')
        page.locator('#feedback-send').click()

        confirm = page.locator('#feedback-confirm')
        expect(confirm).to_be_visible(timeout=5000)
        expect(confirm).to_contain_text('Thanks for your feedback')

    def test_feedback_js_loaded(self, page: Page, test_data):
        """The feedback.js script should be loaded on the page."""
        _pass_email_gate(page, test_data['token_on'], test_data['email_on'])

        # initFeedback should be defined
        result = page.evaluate("typeof initFeedback")
        assert result == 'function'


# ─────────────────────────────────────────────────────────────────────
# Viewer: Feedback-disabled link
# ─────────────────────────────────────────────────────────────────────

class TestViewerFeedbackDisabled:
    """Viewer accessing a feedback-disabled link should NOT see any feedback UI."""

    def test_feedback_button_not_visible(self, page: Page, test_data):
        """The Feedback toggle button should NOT be present in the DOM."""
        _pass_email_gate(page, test_data['token_off'], test_data['email_off'])

        btn = page.locator('#feedback-toggle')
        expect(btn).to_have_count(0)

    def test_feedback_panel_not_in_dom(self, page: Page, test_data):
        """The feedback panel should NOT be in the DOM at all."""
        _pass_email_gate(page, test_data['token_off'], test_data['email_off'])

        panel = page.locator('#feedback-panel')
        expect(panel).to_have_count(0)

    def test_feedback_input_not_in_dom(self, page: Page, test_data):
        """No feedback input or send button should exist."""
        _pass_email_gate(page, test_data['token_off'], test_data['email_off'])

        expect(page.locator('#feedback-input')).to_have_count(0)
        expect(page.locator('#feedback-send')).to_have_count(0)

    def test_feedback_js_not_loaded(self, page: Page, test_data):
        """The feedback.js script should NOT be loaded — initFeedback undefined."""
        _pass_email_gate(page, test_data['token_off'], test_data['email_off'])

        result = page.evaluate("typeof initFeedback")
        assert result == 'undefined'

    def test_deck_still_renders_normally(self, page: Page, test_data):
        """The deck iframe should still load and display content correctly."""
        _pass_email_gate(page, test_data['token_off'], test_data['email_off'])

        iframe = page.frame_locator('#deck-frame')
        heading = iframe.locator('h1', has_text='Slide 1')
        expect(heading).to_be_visible(timeout=5000)

    def test_topbar_still_shows_title_and_logo(self, page: Page, test_data):
        """The topbar should still have the deck title and Synaptiq logo."""
        _pass_email_gate(page, test_data['token_off'], test_data['email_off'])

        title = page.locator('.viewer-topbar-title')
        expect(title).to_be_visible()
        expect(title).to_contain_text('Feedback Toggle Test Deck')

        logo = page.locator('.topbar-logo')
        expect(logo).to_be_visible()


# ─────────────────────────────────────────────────────────────────────
# API enforcement: disabled links reject feedback requests
# ─────────────────────────────────────────────────────────────────────

class TestAPIEnforcementE2E:
    """Feedback API should reject requests made via feedback-disabled links."""

    def _get_view_id_for_link(self, test_data, which):
        """Get or create a view_id for the specified link ('on' or 'off')."""
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        cur = conn.cursor()

        link_id = test_data[f'link_{which}_id']
        email = test_data[f'email_{which}']

        cur.execute(
            "SELECT id FROM views WHERE share_link_id = %s AND viewer_email = %s LIMIT 1",
            (link_id, email)
        )
        view = cur.fetchone()
        if not view:
            cur.execute(
                "INSERT INTO views (share_link_id, viewer_email, user_agent, ip_address, is_forwarded) "
                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (link_id, email, 'E2E-Toggle', '127.0.0.1', False)
            )
            view = cur.fetchone()
            conn.commit()

        view_id = view['id']
        conn.close()
        return view_id

    def test_submit_feedback_blocked_for_disabled_link(self, page: Page, test_data):
        """POST /api/feedback should return 403 when accessed via a disabled link's view."""
        # Pass email gate to establish session
        _pass_email_gate(page, test_data['token_off'], test_data['email_off'])

        view_id = self._get_view_id_for_link(test_data, 'off')

        # Try to submit feedback via fetch in the browser (which has the session)
        result = page.evaluate(f"""
            fetch('/api/feedback', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    view_id: {view_id},
                    slide_number: 1,
                    comment: 'Should be rejected'
                }})
            }}).then(r => ({{ status: r.status, body: r.json() }}))
              .then(async r => ({{ status: r.status, body: await r.body }}))
        """)
        assert result['status'] == 403
        assert 'not enabled' in result['body']['error'].lower()

    def test_get_all_feedback_blocked_for_disabled_link(self, page: Page, test_data):
        """GET /api/feedback/all should return 403 for a disabled link's view."""
        _pass_email_gate(page, test_data['token_off'], test_data['email_off'])

        view_id = self._get_view_id_for_link(test_data, 'off')

        result = page.evaluate(f"""
            fetch('/api/feedback/all?view_id={view_id}')
                .then(r => ({{ status: r.status, body: r.json() }}))
                .then(async r => ({{ status: r.status, body: await r.body }}))
        """)
        assert result['status'] == 403
        assert 'not enabled' in result['body']['error'].lower()

    def test_submit_feedback_allowed_for_enabled_link(self, page: Page, test_data):
        """POST /api/feedback should succeed for an enabled link's view."""
        _pass_email_gate(page, test_data['token_on'], test_data['email_on'])

        view_id = self._get_view_id_for_link(test_data, 'on')

        result = page.evaluate(f"""
            fetch('/api/feedback', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    view_id: {view_id},
                    slide_number: 1,
                    comment: 'API enforcement check - enabled'
                }})
            }}).then(r => ({{ status: r.status, body: r.json() }}))
              .then(async r => ({{ status: r.status, body: await r.body }}))
        """)
        assert result['status'] == 200
        assert result['body']['ok'] is True


# ─────────────────────────────────────────────────────────────────────
# Side-by-side: same deck, two links, different experiences
# ─────────────────────────────────────────────────────────────────────

class TestSideBySideExperience:
    """The same deck should provide different experiences based on the link type."""

    def test_enabled_link_has_feedback_disabled_does_not(self, page: Page, context, test_data):
        """Open the enabled link, confirm feedback exists. Open disabled link in a
        new page, confirm feedback is absent. Same deck, different experiences."""
        # Page 1: feedback-enabled
        _pass_email_gate(page, test_data['token_on'], test_data['email_on'])
        expect(page.locator('#feedback-toggle')).to_be_visible()
        page.locator('#feedback-toggle').click()
        expect(page.locator('#feedback-panel')).to_be_visible()

        # Page 2: feedback-disabled (new page in same context)
        page2 = context.new_page()
        _pass_email_gate(page2, test_data['token_off'], test_data['email_off'])
        expect(page2.locator('#feedback-toggle')).to_have_count(0)
        expect(page2.locator('#feedback-panel')).to_have_count(0)

        # Both should still show the same deck content
        iframe1 = page.frame_locator('#deck-frame')
        iframe2 = page2.frame_locator('#deck-frame')
        expect(iframe1.locator('h1', has_text='Slide 1')).to_be_visible(timeout=5000)
        expect(iframe2.locator('h1', has_text='Slide 1')).to_be_visible(timeout=5000)

        page2.close()

    def test_iframe_takes_full_width_when_feedback_disabled(self, page: Page, test_data):
        """Without feedback, the iframe should occupy the full content width."""
        _pass_email_gate(page, test_data['token_off'], test_data['email_off'])

        iframe = page.locator('#deck-frame')
        content = page.locator('.viewer-content')

        iframe_box = iframe.bounding_box()
        content_box = content.bounding_box()

        # Iframe should be approximately the full width of the content area
        assert iframe_box['width'] >= content_box['width'] - 2  # 2px tolerance
