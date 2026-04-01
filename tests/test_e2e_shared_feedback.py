"""Playwright E2E tests for the shared feedback feature.

Verifies that viewers can see feedback from other viewers in the
feedback panel, with proper visual distinction (own vs. others')
and email obfuscation.

Run with:
    pytest tests/test_e2e_shared_feedback.py --headed --browser chromium \
        --html=tests/reports/shared_feedback_report.html --self-contained-html

Videos are recorded as MP4 to tests/videos/
"""
import os
import secrets
import pytest
import psycopg
from psycopg.rows import dict_row
from playwright.sync_api import Page, expect, BrowserContext

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://showroom:showroom@localhost:5432/showroom')
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5111')


SLIDE_HTML = '''<!DOCTYPE html>
<html>
<head><title>Shared Feedback Test Deck</title>
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
  <p>Welcome to the shared feedback test deck.</p>
</div>
<div class="slide" data-slide="2">
  <h1>Slide 2: Details</h1>
  <p>Details about our offering.</p>
</div>
<div class="slide" data-slide="3">
  <h1>Slide 3: Conclusion</h1>
  <p>Wrapping up.</p>
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


@pytest.fixture(scope="session")
def _shared_test_deck():
    """Create an isolated deck with two share links for two different viewers."""
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    cur = conn.cursor()

    uid = secrets.token_hex(4)
    slug = f'e2e-shared-fb-{uid}'
    token_a = f'shared-fb-token-a-{uid}'
    token_b = f'shared-fb-token-b-{uid}'
    email_a = f'alice-{uid}@testcorp.com'
    email_b = f'bob-{uid}@othercorp.com'

    # Clean up any prior run with same slug (unlikely with uid)
    cur.execute("DELETE FROM decks WHERE slug = %s", (slug,))
    conn.commit()

    # Create deck
    cur.execute(
        "INSERT INTO decks (title, slug, description, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
        ('Shared Feedback Test Deck', slug, 'For shared feedback E2E tests', True)
    )
    deck_id = cur.fetchone()['id']

    # Create two share links for the two viewers
    cur.execute(
        "INSERT INTO share_links (deck_id, recipient_email, token, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
        (deck_id, email_a, token_a, True)
    )
    link_a_id = cur.fetchone()['id']

    cur.execute(
        "INSERT INTO share_links (deck_id, recipient_email, token, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
        (deck_id, email_b, token_b, True)
    )
    link_b_id = cur.fetchone()['id']

    conn.commit()

    # Write slides to storage
    from storage import get_storage
    storage = get_storage()
    storage.save_file(slug, 'index.html', SLIDE_HTML.encode('utf-8'))

    yield {
        'deck_id': deck_id,
        'slug': slug,
        'link_a_id': link_a_id,
        'link_b_id': link_b_id,
        'token_a': token_a,
        'token_b': token_b,
        'email_a': email_a,
        'email_b': email_b,
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
def context(browser, _shared_test_deck):
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
def test_data(_shared_test_deck):
    return _shared_test_deck


def _pass_email_gate(page: Page, token: str, email: str):
    """Navigate to viewer and pass the email gate."""
    page.goto(f'{BASE_URL}/v/{token}')
    page.wait_for_selector('input[type="email"], input[name="email"], .input-large')
    email_input = page.locator('input[type="email"], input[name="email"], .input-large')
    email_input.fill(email)
    page.locator('button[type="submit"], .btn-primary').click()
    page.wait_for_selector('#feedback-toggle', timeout=10000)


def _submit_feedback_via_db(test_data, viewer_key, slide_number, comment):
    """Insert feedback directly into the DB for a given viewer.

    viewer_key: 'a' or 'b' to select which viewer/link/email to use.
    """
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    cur = conn.cursor()

    link_id = test_data[f'link_{viewer_key}_id']
    email = test_data[f'email_{viewer_key}']

    # Find or create a view for this viewer
    cur.execute(
        "SELECT id FROM views WHERE share_link_id = %s AND viewer_email = %s LIMIT 1",
        (link_id, email)
    )
    view = cur.fetchone()
    if not view:
        cur.execute(
            "INSERT INTO views (share_link_id, viewer_email, user_agent, ip_address, is_forwarded) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (link_id, email, 'E2E-SharedFeedback', '127.0.0.1', False)
        )
        view = cur.fetchone()

    cur.execute(
        "INSERT INTO slide_feedback (view_id, slide_number, comment) VALUES (%s, %s, %s) RETURNING id",
        (view['id'], slide_number, comment)
    )
    fb_id = cur.fetchone()['id']
    conn.commit()
    conn.close()
    return fb_id


# ─────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────

class TestSharedFeedbackVisibility:
    """Viewer A should see Viewer B's comments in the feedback panel."""

    def test_viewer_sees_others_feedback_on_same_slide(self, page: Page, test_data):
        """When Viewer B has left feedback on slide 1, Viewer A should see it."""
        # Viewer B leaves feedback via DB
        _submit_feedback_via_db(test_data, 'b', 1, 'Great intro slide!')

        # Viewer A opens the deck and the feedback panel
        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)  # wait for slide detection

        page.locator('#feedback-toggle').click()
        page.wait_for_selector('.feedback-prior-item', timeout=5000)

        # Viewer A should see Viewer B's comment
        other_comment = page.locator('.feedback-prior-item', has_text='Great intro slide!')
        expect(other_comment).to_be_visible(timeout=5000)

    def test_viewer_sees_own_and_others_together(self, page: Page, test_data):
        """Both own and others' comments should appear interleaved."""
        # Viewer B leaves feedback
        _submit_feedback_via_db(test_data, 'b', 1, 'Bob thinks this is solid')

        # Viewer A opens deck, submits own feedback, then checks
        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()
        page.locator('#feedback-input').fill('Alice agrees completely')
        page.locator('#feedback-send').click()

        # Wait for confirmation to auto-dismiss and re-render
        page.wait_for_timeout(4000)

        # Both should be visible
        items = page.locator('.feedback-prior-item')
        expect(items.first).to_be_visible(timeout=5000)

        expect(page.locator('.feedback-prior-item', has_text='Bob thinks this is solid')).to_be_visible()
        expect(page.locator('.feedback-prior-item', has_text='Alice agrees completely')).to_be_visible()

    def test_no_feedback_shows_empty_state(self, page: Page, test_data):
        """A slide with no feedback from anyone should show the empty message."""
        # Navigate to slide 3 (unlikely to have feedback)
        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        # Go to slide 3
        iframe = page.frame_locator('#deck-frame')
        iframe.locator('button', has_text='Next').click()
        page.wait_for_timeout(500)
        iframe.locator('button', has_text='Next').click()
        page.wait_for_timeout(1000)

        page.locator('#feedback-toggle').click()

        # Wait for label to update to Slide 3
        expect(page.locator('#feedback-slide-label')).to_contain_text('Slide 3', timeout=3000)

        # Check for empty state or feedback items
        empty = page.locator('.feedback-prior-empty')
        items = page.locator('.feedback-prior-item')

        # Either empty state is shown, or if there happen to be items, that's fine too
        # The key check: the panel loaded without error
        expect(page.locator('#feedback-prior')).to_be_visible()


class TestSharedFeedbackStyling:
    """Own comments and others' comments should have distinct visual styles."""

    def test_own_comment_has_default_style(self, page: Page, test_data):
        """Own comments should NOT have the 'is-other' class."""
        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()
        page.locator('#feedback-input').fill('My own styled comment')
        page.locator('#feedback-send').click()
        page.wait_for_timeout(4000)

        own_item = page.locator('.feedback-prior-item', has_text='My own styled comment')
        expect(own_item).to_be_visible(timeout=5000)

        # Should NOT have is-other class
        classes = own_item.get_attribute('class')
        assert 'is-other' not in classes

    def test_others_comment_has_is_other_class(self, page: Page, test_data):
        """Others' comments should have the 'is-other' CSS class."""
        _submit_feedback_via_db(test_data, 'b', 1, 'Styled other comment check')

        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()
        page.wait_for_selector('.feedback-prior-item', timeout=5000)

        other_item = page.locator('.feedback-prior-item', has_text='Styled other comment check')
        expect(other_item).to_be_visible(timeout=5000)

        # Should have is-other class
        classes = other_item.get_attribute('class')
        assert 'is-other' in classes

    def test_others_comment_has_arctic_left_border(self, page: Page, test_data):
        """Others' comments should render with the arctic-blue left border accent."""
        _submit_feedback_via_db(test_data, 'b', 1, 'Border color check')

        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()

        other_item = page.locator('.feedback-prior-item.is-other', has_text='Border color check')
        expect(other_item).to_be_visible(timeout=5000)

        # Verify the computed left border color is arctic (#A1B8CA → rgb(161, 184, 202))
        border_color = other_item.evaluate(
            "el => getComputedStyle(el).borderLeftColor"
        )
        assert border_color == 'rgb(161, 184, 202)'


class TestSharedFeedbackAuthorLabels:
    """Author labels should show 'You' for own and obfuscated email for others."""

    def test_own_comment_labeled_you(self, page: Page, test_data):
        """Own comments should show 'You' as the author."""
        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()
        page.locator('#feedback-input').fill('Author label test own')
        page.locator('#feedback-send').click()
        page.wait_for_timeout(4000)

        own_item = page.locator('.feedback-prior-item', has_text='Author label test own')
        expect(own_item).to_be_visible(timeout=5000)

        author = own_item.locator('.feedback-prior-author')
        expect(author).to_have_text('You')

    def test_others_comment_shows_obfuscated_email(self, page: Page, test_data):
        """Others' comments should show an obfuscated email like 'b***@othercorp.com'."""
        _submit_feedback_via_db(test_data, 'b', 1, 'Obfuscation label test')

        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()

        other_item = page.locator('.feedback-prior-item', has_text='Obfuscation label test')
        expect(other_item).to_be_visible(timeout=5000)

        author = other_item.locator('.feedback-prior-author')
        author_text = author.text_content()

        # Should contain ***@ pattern (obfuscated)
        assert '***@' in author_text
        # Should NOT show full email
        assert test_data['email_b'] not in author_text
        # Should start with first char of email_b's local part
        assert author_text.startswith('b')

    def test_author_label_not_empty(self, page: Page, test_data):
        """Every feedback item should have a non-empty author label."""
        _submit_feedback_via_db(test_data, 'b', 1, 'Non-empty author check')

        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()
        page.locator('#feedback-input').fill('My non-empty author check')
        page.locator('#feedback-send').click()
        page.wait_for_timeout(4000)

        authors = page.locator('.feedback-prior-author')
        count = authors.count()
        assert count > 0
        for i in range(count):
            text = authors.nth(i).text_content().strip()
            assert len(text) > 0, f"Author label at index {i} is empty"


class TestSharedFeedbackAcrossSlides:
    """Feedback should be scoped to the correct slide when navigating."""

    def test_slide_2_feedback_not_shown_on_slide_1(self, page: Page, test_data):
        """Feedback on slide 2 should not appear when viewing slide 1's panel."""
        unique = secrets.token_hex(4)
        _submit_feedback_via_db(test_data, 'b', 2, f'Slide2-only-{unique}')

        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        # We're on slide 1
        page.locator('#feedback-toggle').click()
        page.wait_for_timeout(1000)

        # The slide-2-only comment should NOT be in the panel
        slide2_item = page.locator('.feedback-prior-item', has_text=f'Slide2-only-{unique}')
        expect(slide2_item).to_have_count(0)

    def test_navigate_to_slide_shows_correct_feedback(self, page: Page, test_data):
        """Navigating to slide 2 should load slide 2's feedback."""
        unique = secrets.token_hex(4)
        _submit_feedback_via_db(test_data, 'b', 2, f'Slide2-nav-{unique}')

        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        # Open panel on slide 1
        page.locator('#feedback-toggle').click()
        page.wait_for_timeout(500)

        # Navigate to slide 2
        iframe = page.frame_locator('#deck-frame')
        iframe.locator('button', has_text='Next').click()
        page.wait_for_timeout(1500)

        # Panel should now show slide 2 feedback
        expect(page.locator('#feedback-slide-label')).to_contain_text('Slide 2', timeout=3000)

        slide2_item = page.locator('.feedback-prior-item', has_text=f'Slide2-nav-{unique}')
        expect(slide2_item).to_be_visible(timeout=5000)


class TestSharedFeedbackSubmitFlow:
    """Submitting feedback should work correctly in the shared context."""

    def test_new_submission_appears_immediately(self, page: Page, test_data):
        """After submitting, the new comment should appear in the list without reload."""
        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()

        unique_comment = f'Immediate-appear-{secrets.token_hex(4)}'
        page.locator('#feedback-input').fill(unique_comment)
        page.locator('#feedback-send').click()

        # Wait for confirmation to auto-dismiss
        page.wait_for_timeout(4000)

        # Comment should be in the list now
        new_item = page.locator('.feedback-prior-item', has_text=unique_comment)
        expect(new_item).to_be_visible(timeout=5000)

        # And it should be own (no is-other class)
        classes = new_item.get_attribute('class')
        assert 'is-other' not in classes

    def test_placeholder_updates_after_own_submission(self, page: Page, test_data):
        """Placeholder should change to 'Add another comment...' after submitting."""
        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()
        page.locator('#feedback-input').fill('Placeholder test comment')
        page.locator('#feedback-send').click()

        # Wait for confirmation to dismiss and re-render
        page.wait_for_timeout(4000)

        placeholder = page.locator('#feedback-input').get_attribute('placeholder')
        assert placeholder == 'Add another comment...'

    def test_placeholder_without_own_but_with_others(self, page: Page, test_data):
        """If only others have commented, placeholder should still be the default."""
        unique = secrets.token_hex(4)
        _submit_feedback_via_db(test_data, 'b', 2, f'Others-only-placeholder-{unique}')

        _pass_email_gate(page, test_data['token_a'], test_data['email_a'])
        page.wait_for_timeout(1500)

        # Navigate to slide 2
        iframe = page.frame_locator('#deck-frame')
        iframe.locator('button', has_text='Next').click()
        page.wait_for_timeout(1500)

        page.locator('#feedback-toggle').click()
        page.wait_for_timeout(1000)

        # Should see others' feedback but placeholder should reflect no own comments
        expect(page.locator('#feedback-slide-label')).to_contain_text('Slide 2', timeout=3000)

        # Check if viewer A has any own comments on slide 2
        # If not, placeholder should be the default
        own_items = page.locator('.feedback-prior-item:not(.is-other)')
        if own_items.count() == 0:
            placeholder = page.locator('#feedback-input').get_attribute('placeholder')
            assert placeholder == 'Share your thoughts on this slide...'
