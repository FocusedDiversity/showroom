"""Tests for authoring/theme.py — theme engine."""

from authoring.theme import get_synaptiq_theme, get_theme


class TestSynaptiqTheme:
    def test_theme_name(self):
        theme = get_synaptiq_theme()
        assert theme.name == 'synaptiq'

    def test_primary_colors(self):
        theme = get_synaptiq_theme()
        assert theme.primary_colors['soil'] == '#312A29'
        assert theme.primary_colors['apricot'] == '#F7CFA5'
        assert theme.primary_colors['arctic'] == '#A1B8CA'

    def test_font_imports(self):
        theme = get_synaptiq_theme()
        assert 'Zilla+Slab' in theme.font_imports
        assert 'Quicksand' in theme.font_imports
        assert 'Herr+Von+Muellerhoff' in theme.font_imports
        assert 'Abril+Fatface' in theme.font_imports

    def test_font_families(self):
        theme = get_synaptiq_theme()
        assert 'Zilla Slab' in theme.font_families['headline']
        assert 'Quicksand' in theme.font_families['body']

    def test_to_css_contains_colors(self):
        theme = get_synaptiq_theme()
        css = theme.to_css()
        assert '#312A29' in css
        assert '#F7CFA5' in css
        assert '#A1B8CA' in css

    def test_to_css_contains_font_import(self):
        theme = get_synaptiq_theme()
        css = theme.to_css()
        assert "@import url('https://fonts.googleapis.com" in css

    def test_to_css_contains_font_families(self):
        theme = get_synaptiq_theme()
        css = theme.to_css()
        assert "'Zilla Slab'" in css
        assert "'Quicksand'" in css

    def test_to_css_contains_top_bar(self):
        theme = get_synaptiq_theme()
        css = theme.to_css()
        assert 'top-bar' in css
        assert 'linear-gradient' in css

    def test_to_metadata(self):
        theme = get_synaptiq_theme()
        meta = theme.to_metadata()
        assert meta['name'] == 'synaptiq'
        assert meta['primary_colors']['soil'] == '#312A29'
        assert 'logo_svg' in meta
        assert len(meta['logo_svg']) > 100

    def test_logo_svg_present(self):
        theme = get_synaptiq_theme()
        assert '<svg' in theme.logo_svg
        assert 'Synaptiq' in theme.logo_svg


class TestGetTheme:
    def test_default_returns_synaptiq(self):
        theme = get_theme()
        assert theme.name == 'synaptiq'

    def test_explicit_synaptiq(self):
        theme = get_theme('synaptiq')
        assert theme.name == 'synaptiq'

    def test_unknown_falls_back(self):
        theme = get_theme('nonexistent')
        assert theme.name == 'synaptiq'
