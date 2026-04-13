"""Playwright E2E tests for the slide feedback feature.

Run with: pytest tests/test_e2e_feedback.py --headed --browser chromium
Videos are recorded to tests/videos/
"""
import os
import time
import pytest
import psycopg
from psycopg.rows import dict_row
from playwright.sync_api import Page, expect, BrowserContext

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://showroom:showroom@localhost:5432/showroom')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5111')


@pytest.fixture(scope="session")
def _ensure_test_deck():
    """Create a test deck with real HTML slides for E2E testing."""
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    cur = conn.cursor()

    slug = 'e2e-feedback-test-deck'
    token = 'e2e-feedback-test-token'
    email = 'e2e-viewer@test.com'

    # Clean up prior runs
    cur.execute("DELETE FROM decks WHERE slug = %s", (slug,))
    conn.commit()

    # Create deck
    cur.execute(
        "INSERT INTO decks (title, slug, description, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
        ('E2E Feedback Test Deck', slug, 'For Playwright testing', True)
    )
    deck_id = cur.fetchone()['id']

    # Create share link
    cur.execute(
        "INSERT INTO share_links (deck_id, recipient_email, token, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
        (deck_id, email, token, True)
    )
    link_id = cur.fetchone()['id']
    conn.commit()

    # Write a multi-slide HTML deck to storage
    from storage import get_storage
    storage = get_storage()

    slide_html = '''<!DOCTYPE html>
<html>
<head><title>Test Deck</title>
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
  <h1>Slide 1: Introduction</h1>
  <p>Welcome to the E2E test deck.</p>
</div>
<div class="slide" data-slide="2">
  <h1>Slide 2: Details</h1>
  <p>Here are some details about our proposal.</p>
</div>
<div class="slide" data-slide="3">
  <h1>Slide 3: ROI Analysis</h1>
  <p>The projected ROI is 40% over 12 months.</p>
</div>
<div class="slide-indicator">1 / 3</div>
<nav>
  <button onclick="go(-1)">Prev</button>
  <button onclick="go(1)">Next</button>
</nav>
<script>
var current = 1;
var total = 3;
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

    storage.save_file(slug, 'index.html', slide_html.encode('utf-8'))

    yield {
        'deck_id': deck_id,
        'link_id': link_id,
        'token': token,
        'email': email,
        'slug': slug,
    }

    # Cleanup
    cur.execute("DELETE FROM decks WHERE id = %s", (deck_id,))
    conn.commit()
    try:
        storage.delete_deck(slug)
    except Exception:
        pass
    conn.close()


@pytest.fixture
def context(browser, _ensure_test_deck):
    """Browser context with video recording."""
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
def test_data(_ensure_test_deck):
    return _ensure_test_deck


class TestFeedbackE2E:
    """End-to-end tests for the viewer feedback panel."""

    def _pass_email_gate(self, page: Page, token: str, email: str):
        """Navigate to viewer and pass the email gate."""
        page.goto(f'{BASE_URL}/v/{token}')
        page.wait_for_selector('input[type="email"], input[name="email"], .input-large')
        email_input = page.locator('input[type="email"], input[name="email"], .input-large')
        email_input.fill(email)
        page.locator('button[type="submit"], .btn-primary').click()
        # Wait for viewer to load
        page.wait_for_selector('#feedback-toggle', timeout=10000)

    def test_feedback_button_visible_in_viewer(self, page: Page, test_data):
        """The Feedback toggle button should be visible in the viewer topbar."""
        self._pass_email_gate(page, test_data['token'], test_data['email'])

        btn = page.locator('#feedback-toggle')
        expect(btn).to_be_visible()
        expect(btn).to_contain_text('Feedback')

    def test_feedback_panel_opens_and_closes(self, page: Page, test_data):
        """Clicking Feedback opens the panel; clicking again closes it."""
        self._pass_email_gate(page, test_data['token'], test_data['email'])

        panel = page.locator('#feedback-panel')
        btn = page.locator('#feedback-toggle')

        # Initially hidden
        expect(panel).not_to_be_visible()

        # Open
        btn.click()
        expect(panel).to_be_visible()
        expect(page.locator('#feedback-slide-label')).to_be_visible()
        expect(page.locator('#feedback-input')).to_be_visible()

        # Close via button
        btn.click()
        expect(panel).not_to_be_visible()

    def test_submit_feedback_shows_confirmation(self, page: Page, test_data):
        """Submitting feedback shows a thank-you confirmation."""
        self._pass_email_gate(page, test_data['token'], test_data['email'])

        # Wait for slide detection
        page.wait_for_timeout(1500)

        # Open panel and submit
        page.locator('#feedback-toggle').click()
        page.locator('#feedback-input').fill('This introduction slide is excellent!')
        page.locator('#feedback-send').click()

        # Confirmation should appear
        confirm = page.locator('#feedback-confirm')
        expect(confirm).to_be_visible(timeout=5000)
        expect(confirm).to_contain_text('Thanks for your feedback')

    def test_submit_feedback_via_enter_key(self, page: Page, test_data):
        """Pressing Enter in the input field submits feedback."""
        self._pass_email_gate(page, test_data['token'], test_data['email'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()
        input_el = page.locator('#feedback-input')
        input_el.fill('Submitted via Enter key')
        input_el.press('Enter')

        confirm = page.locator('#feedback-confirm')
        expect(confirm).to_be_visible(timeout=5000)

    def test_prior_feedback_shown_on_reopen(self, page: Page, test_data):
        """After submitting, reopening the panel on the same slide shows prior feedback."""
        self._pass_email_gate(page, test_data['token'], test_data['email'])
        page.wait_for_timeout(1500)

        # Submit feedback
        page.locator('#feedback-toggle').click()
        page.locator('#feedback-input').fill('Prior feedback test')
        page.locator('#feedback-send').click()

        # Wait for confirmation to auto-dismiss
        page.wait_for_timeout(4000)

        # Check prior feedback is shown (may not be first due to shared feedback)
        prior = page.locator('.feedback-prior-item')
        expect(prior.first).to_be_visible(timeout=5000)
        expect(page.locator('.feedback-prior-item', has_text='Prior feedback test')).to_be_visible(timeout=5000)

    def test_navigate_slide_and_submit(self, page: Page, test_data):
        """Navigate to slide 2, submit feedback, verify slide label updates."""
        self._pass_email_gate(page, test_data['token'], test_data['email'])
        page.wait_for_timeout(1500)

        # Navigate to slide 2 via the iframe
        iframe = page.frame_locator('#deck-frame')
        iframe.locator('button', has_text='Next').click()
        page.wait_for_timeout(1000)

        # Open feedback panel
        page.locator('#feedback-toggle').click()

        # The label should reference slide 2
        label = page.locator('#feedback-slide-label')
        expect(label).to_contain_text('Slide 2', timeout=3000)

        # Submit
        page.locator('#feedback-input').fill('Slide 2 looks good')
        page.locator('#feedback-send').click()

        confirm = page.locator('#feedback-confirm')
        expect(confirm).to_be_visible(timeout=5000)
        expect(confirm).to_contain_text('Slide 2')

    def test_close_panel_via_x_button(self, page: Page, test_data):
        """Clicking the X button closes the feedback panel."""
        self._pass_email_gate(page, test_data['token'], test_data['email'])

        page.locator('#feedback-toggle').click()
        panel = page.locator('#feedback-panel')
        expect(panel).to_be_visible()

        page.locator('#feedback-close').click()
        expect(panel).not_to_be_visible()


class TestAnalyticsFeedbackTabE2E:
    """E2E tests for the analytics feedback tab."""

    def _submit_feedback_via_api(self, test_data):
        """Submit feedback directly via the DB for analytics testing."""
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        cur = conn.cursor()

        # Ensure a view exists
        cur.execute(
            "SELECT id FROM views WHERE share_link_id = %s LIMIT 1",
            (test_data['link_id'],)
        )
        view = cur.fetchone()
        if not view:
            cur.execute(
                "INSERT INTO views (share_link_id, viewer_email, user_agent, ip_address, is_forwarded, current_slide, total_slides) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                (test_data['link_id'], test_data['email'], 'E2E', '127.0.0.1', False, 1, 3)
            )
            view = cur.fetchone()

        view_id = view['id']

        # Insert feedback
        for slide, comment in [(1, 'E2E analytics feedback slide 1'), (2, 'E2E analytics feedback slide 2')]:
            cur.execute(
                "INSERT INTO slide_feedback (view_id, slide_number, comment) VALUES (%s, %s, %s)",
                (view_id, slide, comment)
            )
        conn.commit()
        conn.close()

    def test_analytics_feedback_tab_visible(self, page: Page, test_data):
        """The Feedback tab should be visible on the analytics page."""
        self._submit_feedback_via_api(test_data)

        page.goto(f'{BASE_URL}/admin/deck/{test_data["deck_id"]}/analytics')
        page.wait_for_selector('.analytics-tab', timeout=10000)

        feedback_tab = page.locator('.analytics-tab', has_text='Feedback')
        expect(feedback_tab).to_be_visible()

    def test_analytics_feedback_tab_shows_data(self, page: Page, test_data):
        """Clicking the Feedback tab shows the feedback table with data."""
        self._submit_feedback_via_api(test_data)

        page.goto(f'{BASE_URL}/admin/deck/{test_data["deck_id"]}/analytics')
        page.wait_for_selector('.analytics-tab', timeout=10000)

        # Click Feedback tab
        page.locator('.analytics-tab', has_text='Feedback').click()

        # Table should be visible with data
        table = page.locator('#feedback-table')
        expect(table).to_be_visible(timeout=5000)

        # Should have feedback rows
        rows = page.locator('#feedback-tbody tr')
        expect(rows.first).to_be_visible(timeout=5000)

    def test_analytics_feedback_stat_card(self, page: Page, test_data):
        """The Feedback Items stat card should show the count."""
        self._submit_feedback_via_api(test_data)

        page.goto(f'{BASE_URL}/admin/deck/{test_data["deck_id"]}/analytics')
        page.wait_for_selector('#stat-feedback', timeout=10000)

        stat = page.locator('#stat-feedback')
        # Should show a number > 0
        page.wait_for_function(
            "document.getElementById('stat-feedback').textContent !== '-'",
            timeout=5000
        )
        text = stat.text_content()
        assert text.strip() != '-'
        assert int(text.strip()) > 0

    def test_analytics_feedback_filter_by_slide(self, page: Page, test_data):
        """Slide filter should filter the feedback table."""
        self._submit_feedback_via_api(test_data)

        page.goto(f'{BASE_URL}/admin/deck/{test_data["deck_id"]}/analytics')
        page.wait_for_selector('.analytics-tab', timeout=10000)
        page.locator('.analytics-tab', has_text='Feedback').click()
        page.wait_for_selector('#feedback-filter-slide', timeout=5000)

        # Filter to slide 1
        page.locator('#feedback-filter-slide').select_option(label='Slide 1')
        page.wait_for_timeout(500)

        # All visible rows should have slide badge "1"
        badges = page.locator('#feedback-tbody .slide-badge')
        count = badges.count()
        assert count > 0
        for i in range(count):
            assert badges.nth(i).text_content().strip() == '1'
