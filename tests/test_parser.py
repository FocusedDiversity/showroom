"""Tests for authoring/parser.py — markdown-to-slides content parser."""

import pytest
from authoring.parser import parse_markdown, Slide, list_models, model_to_markdown_template


class TestBasicParsing:
    def test_empty_input(self):
        assert parse_markdown('') == []
        assert parse_markdown(None) == []
        assert parse_markdown('   ') == []

    def test_single_title_slide(self):
        md = '# My Deck\n\nSubtitle text here.'
        slides = parse_markdown(md)
        assert len(slides) == 1
        assert slides[0].is_title_slide is True
        assert slides[0].title == 'My Deck'
        assert slides[0].subtitle == 'Subtitle text here.'
        assert slides[0].layout_hint == 'title'

    def test_h2_splitting(self):
        md = """# Deck Title

Subtitle

## First Section

Some content.

## Second Section

More content.
"""
        slides = parse_markdown(md)
        assert len(slides) == 3
        assert slides[0].is_title_slide is True
        assert slides[0].title == 'Deck Title'
        assert slides[1].title == 'First Section'
        assert slides[1].is_title_slide is False
        assert slides[2].title == 'Second Section'

    def test_horizontal_rule_splitting(self):
        md = """# Deck Title

Subtitle

---

## Section One

Content A.

---

## Section Two

Content B.
"""
        slides = parse_markdown(md)
        assert len(slides) == 3
        assert slides[0].title == 'Deck Title'
        assert slides[1].title == 'Section One'
        assert slides[2].title == 'Section Two'


class TestLayoutDetection:
    def test_text_layout(self):
        md = """# Title

Sub

## Overview

This is a paragraph of text explaining the project.
It has multiple lines but no special structure.
"""
        slides = parse_markdown(md)
        assert slides[1].layout_hint == 'text'

    def test_cards_layout_from_bullets(self):
        md = """# Title

Sub

## Features

- Feature one with description
- Feature two with description
- Feature three with description
- Feature four with description
- Feature five with description
- Feature six with description
"""
        slides = parse_markdown(md)
        assert slides[1].layout_hint == 'cards'

    def test_cards_layout_from_h3(self):
        md = """# Title

Sub

## Capabilities

### Data Ingestion
Process data from multiple sources.

### Model Training
Train ML models at scale.

### Deployment
Deploy models to production.
"""
        slides = parse_markdown(md)
        assert slides[1].layout_hint == 'cards'

    def test_timeline_layout(self):
        md = """# Title

Sub

## Project Plan

1. Phase one: Discovery and assessment
2. Phase two: Design and prototyping
3. Phase three: Implementation
4. Phase four: Testing and deployment
"""
        slides = parse_markdown(md)
        assert slides[1].layout_hint == 'timeline'

    def test_timeline_from_keywords(self):
        md = """# Title

Sub

## Schedule

Week 1-2: Discovery sessions
Week 3-4: Data analysis
Week 5-6: Model development
Week 7-8: Integration testing
"""
        slides = parse_markdown(md)
        assert slides[1].layout_hint == 'timeline'

    def test_stats_layout(self):
        md = """# Title

Sub

## Key Metrics

$1.2M revenue impact
95% accuracy achieved
3x faster processing
42% cost reduction
"""
        slides = parse_markdown(md)
        assert slides[1].layout_hint == 'stats'

    def test_split_layout_with_blockquote(self):
        md = """# Title

Sub

## Client Feedback

> "This solution transformed our operations."

The client saw immediate results after the first phase.
Their team adopted the new workflow within two weeks.
"""
        slides = parse_markdown(md)
        assert slides[1].layout_hint == 'split'


class TestItemExtraction:
    def test_bullet_items(self):
        md = """# Title

Sub

## Deliverables

- Data governance framework
- AI readiness assessment
- Implementation roadmap
"""
        slides = parse_markdown(md)
        assert len(slides[1].items) == 3
        assert slides[1].items[0] == 'Data governance framework'

    def test_numbered_items(self):
        md = """# Title

Sub

## Steps

1. Assess current state
2. Define target state
3. Build roadmap
"""
        slides = parse_markdown(md)
        assert len(slides[1].items) == 3
        assert slides[1].items[0] == 'Assess current state'


class TestModelIntegration:
    def test_list_models(self):
        models = list_models()
        # Should find at least the sales group with quote model
        assert 'sales' in models
        assert any(m['name'] == 'quote' for m in models['sales'])

    def test_model_to_markdown_template_unknown(self):
        template = model_to_markdown_template('nonexistent-model')
        assert '# Nonexistent Model' in template

    def test_model_to_markdown_template_quote(self):
        template = model_to_markdown_template('quote')
        assert '#' in template  # Should have at least a title
        assert len(template) > 50  # Should have meaningful content


class TestQuoteModelParsing:
    """Test parsing markdown structured like the quote deliverable model."""

    def test_quote_deck(self):
        md = """# Data Governance Foundation

A proposal for building enterprise data governance at Acme Corp.

## Business Problem

Acme Corp lacks a unified data governance strategy, leading to
inconsistent data quality across departments and compliance risks.

## Use Case

As a Chief Data Officer, I will implement a data governance framework
that ensures data quality, compliance, and accessibility across all
departments.

## Proposed Schedule

1. Week 1-2: Discovery and current state assessment
2. Week 3-4: Framework design and stakeholder alignment
3. Week 5-6: Implementation planning and quick wins
4. Week 7-8: Rollout and change management

## Acceptance Criteria

- Data governance framework documented and approved
- Quality metrics defined for top 10 data assets
- Compliance gaps identified and remediation plan created
- Executive readout delivered
"""
        slides = parse_markdown(md, model_name='quote')
        assert len(slides) == 5
        assert slides[0].is_title_slide is True
        assert slides[0].title == 'Data Governance Foundation'
        assert slides[0].subtitle == 'A proposal for building enterprise data governance at Acme Corp.'
        assert slides[1].title == 'Business Problem'
        assert slides[1].layout_hint == 'text'
        assert slides[3].layout_hint == 'timeline'
        assert slides[4].layout_hint == 'cards'
        assert len(slides[4].items) == 4
