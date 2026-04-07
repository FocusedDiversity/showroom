"""
Playwright UI tests for the deck-authoring capability.

Tests cover every requirement from the design document:
1. Authoring form (model selection, markdown input, theme, collage)
2. Variant preview and selection
3. Refinement with feedback loop
4. Publishing to Showroom
5. Dashboard integration (Create New Deck button, in-progress sessions)
6. Generated deck rendering (navigation, branding, slide layouts)
"""

import re
import pytest
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5001"

SAMPLE_MARKDOWN = """# Data Governance Foundation

A proposal for building enterprise data governance at Acme Corp.

## Business Problem

Acme Corp lacks a unified data governance strategy, leading to
inconsistent data quality across departments and **compliance risks**.

## Key Metrics

$1.2M revenue at risk
95% of departments affected
3x duplicate data processing
42% compliance gap

## Proposed Approach

### Discovery & Assessment
Comprehensive audit of current data assets, quality, and governance.

### Framework Design
Design a governance framework aligned with industry standards.

### Implementation
Roll out policies, tools, and training across all departments.

## Project Timeline

1. Week 1-2: Discovery and current state assessment
2. Week 3-4: Framework design and stakeholder alignment
3. Week 5-6: Implementation planning and quick wins
4. Week 7-8: Rollout and change management

## Thank You

We look forward to partnering with Acme Corp on this journey.
"""


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


# ══════════════════════════════════════════════════════════════════════
# 1. DASHBOARD INTEGRATION
# ══════════════════════════════════════════════════════════════════════

class TestDashboard:
    def test_dashboard_has_create_new_deck_button(self, page):
        """Dashboard shows 'Create New Deck' button linking to author form."""
        page.goto(f"{BASE_URL}/admin")
        btn = page.locator("a:has-text('Create New Deck')")
        expect(btn).to_be_visible()
        expect(btn).to_have_attribute("href", re.compile(r"/admin/author"))

    def test_dashboard_has_upload_html_button(self, page):
        """Dashboard still has the original Upload HTML button."""
        page.goto(f"{BASE_URL}/admin")
        btn = page.locator("button:has-text('Upload HTML')")
        expect(btn).to_be_visible()

    def test_navbar_has_author_link(self, page):
        """Navigation bar includes an 'Author' link."""
        page.goto(f"{BASE_URL}/admin")
        link = page.locator("nav a:has-text('Author')")
        expect(link).to_be_visible()
        expect(link).to_have_attribute("href", re.compile(r"/admin/author"))


# ══════════════════════════════════════════════════════════════════════
# 2. AUTHORING FORM
# ══════════════════════════════════════════════════════════════════════

class TestAuthoringForm:
    def test_form_loads(self, page):
        """Author form page loads with all required elements."""
        page.goto(f"{BASE_URL}/admin/author")
        expect(page.locator("h1:has-text('Create New Deck')")).to_be_visible()

    def test_model_dropdown_has_groups(self, page):
        """Model dropdown shows sales and delivery groups."""
        page.goto(f"{BASE_URL}/admin/author")
        select = page.locator("#model_name")
        expect(select).to_be_visible()

        # Check optgroups exist
        sales_group = page.locator("optgroup[label='Sales']")
        delivery_group = page.locator("optgroup[label='Delivery']")
        expect(sales_group).to_have_count(1)
        expect(delivery_group).to_have_count(1)

    def test_model_dropdown_has_all_models(self, page):
        """All 6 deliverable models appear in the dropdown."""
        page.goto(f"{BASE_URL}/admin/author")
        options = page.locator("#model_name option")
        # 1 (custom) + 3 sales + 3 delivery = 7
        expect(options).to_have_count(7)

    def test_model_selection_prefills_template(self, page):
        """Selecting a model pre-fills the markdown textarea."""
        page.goto(f"{BASE_URL}/admin/author")
        textarea = page.locator("#markdown_content")

        # Initially should be empty or have placeholder
        initial_value = textarea.input_value()

        # Select kick-off model
        page.locator("#model_name").select_option("kick-off")
        page.wait_for_timeout(500)  # Wait for AJAX

        new_value = textarea.input_value()
        assert "Project Kick-Off" in new_value or "Project Overview" in new_value
        assert len(new_value) > len(initial_value)

    def test_model_discovery_template(self, page):
        """Discovery model template includes expected sections."""
        page.goto(f"{BASE_URL}/admin/author")
        page.locator("#model_name").select_option("discovery")
        page.wait_for_timeout(500)
        value = page.locator("#markdown_content").input_value()
        assert "Current State" in value
        assert "Pain Points" in value

    def test_model_progress_report_template(self, page):
        """Progress report model template includes expected sections."""
        page.goto(f"{BASE_URL}/admin/author")
        page.locator("#model_name").select_option("progress-report")
        page.wait_for_timeout(500)
        value = page.locator("#markdown_content").input_value()
        assert "Accomplishments" in value
        assert "Risks" in value

    def test_theme_dropdown_present(self, page):
        """Theme dropdown shows Synaptiq Default option."""
        page.goto(f"{BASE_URL}/admin/author")
        select = page.locator("#theme_name")
        expect(select).to_be_visible()
        option = page.locator("#theme_name option[value='synaptiq']")
        expect(option).to_have_count(1)

    def test_theme_color_swatches(self, page):
        """Theme preview shows color swatches."""
        page.goto(f"{BASE_URL}/admin/author")
        swatches = page.locator(".theme-swatch")
        expect(swatches).to_have_count(6)

    def test_collage_radio_options(self, page):
        """Three collage mode radio options exist: none, existing, generate."""
        page.goto(f"{BASE_URL}/admin/author")
        radios = page.locator("input[name='collage_mode']")
        expect(radios).to_have_count(3)

    def test_collage_gallery_hidden_by_default(self, page):
        """Collage gallery is hidden until 'Select from library' is chosen."""
        page.goto(f"{BASE_URL}/admin/author")
        gallery = page.locator("#collageGallery")
        expect(gallery).to_be_hidden()

    def test_collage_gallery_shows_on_radio(self, page):
        """Clicking 'Select from library' shows the gallery."""
        page.goto(f"{BASE_URL}/admin/author")
        page.locator("input[value='existing']").click()
        gallery = page.locator("#collageGallery")
        expect(gallery).to_be_visible()

    def test_collage_generate_shows_on_radio(self, page):
        """Clicking 'Generate with AI' shows the generate panel."""
        page.goto(f"{BASE_URL}/admin/author")
        page.locator("input[value='generate']").click()
        panel = page.locator("#collageGenerate")
        expect(panel).to_be_visible()

    def test_markdown_textarea_present(self, page):
        """Markdown textarea exists and is editable."""
        page.goto(f"{BASE_URL}/admin/author")
        textarea = page.locator("#markdown_content")
        expect(textarea).to_be_visible()
        textarea.fill("# Test")
        assert textarea.input_value() == "# Test"

    def test_generate_previews_button(self, page):
        """Generate Previews button exists."""
        page.goto(f"{BASE_URL}/admin/author")
        btn = page.locator("#generateBtn")
        expect(btn).to_be_visible()
        expect(btn).to_contain_text("Generate Previews")

    def test_back_to_dashboard_link(self, page):
        """Cancel button links back to dashboard."""
        page.goto(f"{BASE_URL}/admin/author")
        cancel = page.locator("a:has-text('Cancel')")
        expect(cancel).to_be_visible()

    def test_empty_content_shows_error(self, page):
        """Submitting with empty content shows an error flash."""
        page.goto(f"{BASE_URL}/admin/author")
        page.locator("#generateBtn").click()
        page.wait_for_load_state("networkidle")
        # Should redirect back with error flash
        expect(page.locator(".flash-error")).to_be_visible()


# ══════════════════════════════════════════════════════════════════════
# 3. END-TO-END: GENERATE → PREVIEW → REFINE → PUBLISH
# ══════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    def _submit_content(self, page):
        """Helper: fill and submit the authoring form."""
        page.goto(f"{BASE_URL}/admin/author")
        page.locator("#markdown_content").fill(SAMPLE_MARKDOWN)
        page.locator("#generateBtn").click()
        page.wait_for_load_state("networkidle")

    def test_generate_redirects_to_preview(self, page):
        """Submitting content redirects to the preview page."""
        self._submit_content(page)
        expect(page).to_have_url(re.compile(r"/admin/author/preview/\d+"))

    def test_preview_shows_variants(self, page):
        """Preview page shows 3 variant cards."""
        self._submit_content(page)
        cards = page.locator(".variant-card")
        expect(cards).to_have_count(3)

    def test_preview_has_select_buttons(self, page):
        """Each variant has a 'Select This' button."""
        self._submit_content(page)
        select_btns = page.locator("button:has-text('Select This')")
        expect(select_btns).to_have_count(3)

    def test_preview_has_full_preview_links(self, page):
        """Each variant has a 'Preview Full' link."""
        self._submit_content(page)
        preview_links = page.locator("a:has-text('Preview Full')")
        expect(preview_links).to_have_count(3)

    def test_preview_iframes_load(self, page):
        """Variant preview iframes exist."""
        self._submit_content(page)
        iframes = page.locator("iframe.variant-preview")
        expect(iframes).to_have_count(3)

    def test_full_preview_opens_deck(self, page):
        """Clicking 'Preview Full' opens a working deck in new tab."""
        self._submit_content(page)
        # Get the href of the first preview link
        href = page.locator("a:has-text('Preview Full')").first.get_attribute("href")
        # Navigate to it directly
        page.goto(f"{BASE_URL}{href}")
        # Should be a full deck with slides
        expect(page.locator(".slide")).to_have_count(6, timeout=5000)

    def test_select_variant_redirects_to_refine(self, page):
        """Selecting a variant redirects to the refinement view."""
        self._submit_content(page)
        page.locator("button:has-text('Select This')").first.click()
        page.wait_for_load_state("networkidle")
        expect(page).to_have_url(re.compile(r"/admin/author/refine/\d+"))

    def test_refine_view_has_preview_iframe(self, page):
        """Refinement view shows the selected deck in an iframe."""
        self._submit_content(page)
        page.locator("button:has-text('Select This')").first.click()
        page.wait_for_load_state("networkidle")
        iframe = page.locator("iframe.preview-frame")
        expect(iframe).to_be_visible()

    def test_refine_view_has_feedback_textarea(self, page):
        """Refinement view has a feedback textarea."""
        self._submit_content(page)
        page.locator("button:has-text('Select This')").first.click()
        page.wait_for_load_state("networkidle")
        textarea = page.locator("textarea[name='feedback_text']")
        expect(textarea).to_be_visible()

    def test_refine_view_has_quick_action_buttons(self, page):
        """Refinement view has quick action buttons."""
        self._submit_content(page)
        page.locator("button:has-text('Select This')").first.click()
        page.wait_for_load_state("networkidle")
        quick_btns = page.locator(".quick-btn")
        assert quick_btns.count() >= 4

    def test_quick_action_populates_feedback(self, page):
        """Clicking a quick action button populates the feedback textarea."""
        self._submit_content(page)
        page.locator("button:has-text('Select This')").first.click()
        page.wait_for_load_state("networkidle")
        page.locator(".quick-btn").first.click()
        value = page.locator("textarea[name='feedback_text']").input_value()
        assert len(value) > 0

    def test_apply_feedback_increments_revision(self, page):
        """Applying feedback creates a feedback history entry and updates revision."""
        self._submit_content(page)
        page.locator("button:has-text('Select This')").first.click()
        page.wait_for_load_state("networkidle")
        page.locator("textarea[name='feedback_text']").fill("Make colors warmer")
        page.locator("button:has-text('Apply Changes')").click()
        page.wait_for_load_state("networkidle")
        # Should still be on the refine page
        expect(page).to_have_url(re.compile(r"/admin/author/refine/\d+"))
        # Feedback history should appear with the feedback text
        expect(page.locator(".feedback-item")).to_have_count(1, timeout=5000)
        expect(page.locator(".feedback-item")).to_contain_text("Make colors warmer")

    def test_refine_has_publish_button(self, page):
        """Refinement view has a 'Publish to Showroom' button."""
        self._submit_content(page)
        page.locator("button:has-text('Select This')").first.click()
        page.wait_for_load_state("networkidle")
        btn = page.locator("button:has-text('Publish to Showroom')")
        expect(btn).to_be_visible()

    def test_publish_modal_opens(self, page):
        """Clicking Publish opens a confirmation modal."""
        self._submit_content(page)
        page.locator("button:has-text('Select This')").first.click()
        page.wait_for_load_state("networkidle")
        page.locator("button:has-text('Publish to Showroom')").click()
        modal = page.locator("#publishModal")
        expect(modal).to_be_visible()
        expect(page.locator("#pub_title")).to_be_visible()
        expect(page.locator("#pub_desc")).to_be_visible()

    def test_publish_creates_deck(self, page):
        """Publishing creates a deck and redirects to deck detail."""
        self._submit_content(page)
        page.locator("button:has-text('Select This')").first.click()
        page.wait_for_load_state("networkidle")
        page.locator("button:has-text('Publish to Showroom')").click()
        page.wait_for_timeout(300)
        page.locator("#pub_title").fill("E2E Test Deck")
        page.locator("#pub_desc").fill("Created by Playwright test")
        page.locator("#publishModal button:has-text('Publish')").click()
        page.wait_for_load_state("networkidle")
        # Should redirect to deck detail
        expect(page).to_have_url(re.compile(r"/admin/deck/\d+"))
        expect(page.locator("h1")).to_contain_text("E2E Test Deck")


# ══════════════════════════════════════════════════════════════════════
# 4. GENERATED DECK RENDERING
# ══════════════════════════════════════════════════════════════════════

class TestGeneratedDeck:
    def _get_deck_url(self, page):
        """Generate a deck and return the preview URL."""
        page.goto(f"{BASE_URL}/admin/author")
        page.locator("#markdown_content").fill(SAMPLE_MARKDOWN)
        page.locator("#generateBtn").click()
        page.wait_for_load_state("networkidle")
        href = page.locator("a:has-text('Preview Full')").first.get_attribute("href")
        return f"{BASE_URL}{href}"

    def test_deck_has_correct_slide_count(self, page):
        """Generated deck has the expected number of slides."""
        url = self._get_deck_url(page)
        page.goto(url)
        slides = page.locator(".slide")
        expect(slides).to_have_count(6)

    def test_deck_has_nav_bar(self, page):
        """Generated deck has navigation bar with prev/next buttons."""
        url = self._get_deck_url(page)
        page.goto(url)
        expect(page.locator(".nav-bar")).to_be_visible()
        expect(page.locator("#prevBtn")).to_be_visible()
        expect(page.locator("#nextBtn")).to_be_visible()

    def test_deck_has_nav_dots(self, page):
        """Generated deck has navigation dots for each slide."""
        url = self._get_deck_url(page)
        page.goto(url)
        dots = page.locator(".nav-dot")
        expect(dots).to_have_count(6)

    def test_deck_first_slide_active(self, page):
        """First slide is active on load."""
        url = self._get_deck_url(page)
        page.goto(url)
        active = page.locator(".slide.active")
        expect(active).to_have_count(1)

    def test_deck_keyboard_navigation(self, page):
        """Arrow keys navigate between slides."""
        url = self._get_deck_url(page)
        page.goto(url)
        # Initial state: slide 1/6
        expect(page.locator("#slideNum")).to_contain_text("1 / 6")
        # Press right arrow
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(200)
        expect(page.locator("#slideNum")).to_contain_text("2 / 6")
        # Press right again
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(200)
        expect(page.locator("#slideNum")).to_contain_text("3 / 6")
        # Press left
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(200)
        expect(page.locator("#slideNum")).to_contain_text("2 / 6")

    def test_deck_button_navigation(self, page):
        """Prev/Next buttons navigate between slides."""
        url = self._get_deck_url(page)
        page.goto(url)
        page.locator("#nextBtn").click()
        page.wait_for_timeout(200)
        expect(page.locator("#slideNum")).to_contain_text("2 / 6")
        page.locator("#prevBtn").click()
        page.wait_for_timeout(200)
        expect(page.locator("#slideNum")).to_contain_text("1 / 6")

    def test_deck_has_top_bar_gradient(self, page):
        """Each slide has the brand top bar gradient."""
        url = self._get_deck_url(page)
        page.goto(url)
        top_bars = page.locator(".top-bar")
        assert top_bars.count() >= 6

    def test_deck_title_slide_has_brand_elements(self, page):
        """Title slide contains the deck title and Synaptiq branding."""
        url = self._get_deck_url(page)
        page.goto(url)
        title_slide = page.locator(".s-title")
        expect(title_slide).to_be_visible()
        expect(title_slide.locator("h1")).to_contain_text("Data Governance Foundation")
        expect(title_slide.locator(".aiq-tag")).to_contain_text("HUMANKIND OF AI")

    def test_deck_uses_correct_fonts(self, page):
        """Deck uses Zilla Slab for headlines and Quicksand for body."""
        url = self._get_deck_url(page)
        page.goto(url)
        # Check that the font import exists in the page
        html = page.content()
        assert "Zilla+Slab" in html or "Zilla Slab" in html
        assert "Quicksand" in html

    def test_deck_uses_brand_colors(self, page):
        """Deck uses Synaptiq brand colors (Soil, Arctic, Apricot)."""
        url = self._get_deck_url(page)
        page.goto(url)
        html = page.content()
        assert "#312A29" in html  # Soil
        assert "#A1B8CA" in html  # Arctic
        assert "#F7CFA5" in html  # Apricot

    def test_deck_has_slide_indicator(self, page):
        """Deck shows slide number indicator."""
        url = self._get_deck_url(page)
        page.goto(url)
        indicator = page.locator("#slideNum")
        expect(indicator).to_be_visible()
        expect(indicator).to_contain_text("1 / 6")


# ══════════════════════════════════════════════════════════════════════
# 5. DASHBOARD SHOWS IN-PROGRESS SESSIONS
# ══════════════════════════════════════════════════════════════════════

class TestDashboardSessions:
    def test_in_progress_sessions_visible(self, page):
        """Dashboard shows in-progress authoring sessions after generating."""
        # First, create a session by generating (but not publishing)
        page.goto(f"{BASE_URL}/admin/author")
        page.locator("#markdown_content").fill("# Test Session\n\nContent here.\n\n## Section\n\nMore content.")
        page.locator("#generateBtn").click()
        page.wait_for_load_state("networkidle")

        # Go to dashboard
        page.goto(f"{BASE_URL}/admin")
        # Should show in-progress section
        session_cards = page.locator("text=In-Progress Decks")
        expect(session_cards).to_be_visible()


# ══════════════════════════════════════════════════════════════════════
# 6. MODEL TEMPLATE API
# ══════════════════════════════════════════════════════════════════════

class TestModelTemplateAPI:
    def test_api_returns_json(self, page):
        """Model template API returns JSON with template content."""
        response = page.request.get(f"{BASE_URL}/admin/author/model-template?model=kick-off")
        assert response.status == 200
        data = response.json()
        assert "template" in data
        assert "Project Kick-Off" in data["template"]

    def test_api_empty_model_returns_empty(self, page):
        """Empty model name returns empty template."""
        response = page.request.get(f"{BASE_URL}/admin/author/model-template?model=")
        assert response.status == 200
        data = response.json()
        assert data["template"] == ""

    def test_api_all_models_return_content(self, page):
        """All 6 models return non-empty templates."""
        models = ["quote", "discovery", "design", "kick-off", "progress-report", "strategy-deliverable"]
        for model in models:
            response = page.request.get(f"{BASE_URL}/admin/author/model-template?model={model}")
            assert response.status == 200
            data = response.json()
            assert len(data["template"]) > 50, f"Model {model} returned short template"
