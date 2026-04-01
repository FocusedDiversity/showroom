"""Unit tests for the slide feedback feature.

Tests API validation, session checks, and response formats
without relying on specific database state.
"""
import json
import pytest


class TestSubmitFeedbackValidation:
    """POST /api/feedback — input validation and session checks."""

    def test_missing_json_body(self, client):
        resp = client.post('/api/feedback', content_type='application/json')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['ok'] is False

    def test_empty_json_body(self, client):
        resp = client.post('/api/feedback', json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['ok'] is False

    def test_missing_view_id(self, client):
        resp = client.post('/api/feedback', json={
            'slide_number': 1, 'comment': 'test'
        })
        assert resp.status_code == 400

    def test_missing_slide_number(self, client):
        resp = client.post('/api/feedback', json={
            'view_id': 1, 'comment': 'test'
        })
        assert resp.status_code == 400

    def test_missing_comment(self, client):
        resp = client.post('/api/feedback', json={
            'view_id': 1, 'slide_number': 1
        })
        assert resp.status_code == 400

    def test_empty_comment(self, client):
        resp = client.post('/api/feedback', json={
            'view_id': 1, 'slide_number': 1, 'comment': '   '
        })
        assert resp.status_code == 400

    def test_comment_too_long(self, client):
        resp = client.post('/api/feedback', json={
            'view_id': 1, 'slide_number': 1, 'comment': 'x' * 1001
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'too long' in data['error']

    def test_invalid_slide_number_zero(self, client):
        resp = client.post('/api/feedback', json={
            'view_id': 1, 'slide_number': 0, 'comment': 'test'
        })
        assert resp.status_code == 400

    def test_invalid_slide_number_negative(self, client):
        resp = client.post('/api/feedback', json={
            'view_id': 1, 'slide_number': -1, 'comment': 'test'
        })
        assert resp.status_code == 400

    def test_nonexistent_view_id(self, client):
        """A view_id that doesn't exist should return 404."""
        resp = client.post('/api/feedback', json={
            'view_id': 999999, 'slide_number': 1, 'comment': 'test'
        })
        assert resp.status_code == 404

    def test_no_session_returns_403(self, client, seed_deck):
        """Without a viewer session, should get 403."""
        resp = client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 1,
            'comment': 'test without session'
        })
        assert resp.status_code == 403

    def test_wrong_session_email_returns_403(self, client, seed_deck):
        """Session email doesn't match the view's viewer_email."""
        with client.session_transaction() as sess:
            sess[f"viewer_email_{seed_deck['token']}"] = 'wrong@email.com'

        resp = client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 1,
            'comment': 'test wrong session'
        })
        assert resp.status_code == 403


class TestGetFeedbackValidation:
    """GET /api/feedback — input validation."""

    def test_missing_view_id_param(self, client):
        resp = client.get('/api/feedback')
        assert resp.status_code == 400

    def test_nonexistent_view_id(self, client):
        resp = client.get('/api/feedback?view_id=999999')
        assert resp.status_code == 404

    def test_no_session_returns_403(self, client, seed_deck):
        resp = client.get(f'/api/feedback?view_id={seed_deck["view_id"]}')
        assert resp.status_code == 403


class TestCommentEdgeCases:
    """Edge cases for comment content."""

    def test_max_length_comment_accepted(self, client, seed_deck):
        """Exactly 1000 chars should be accepted."""
        with client.session_transaction() as sess:
            sess[f"viewer_email_{seed_deck['token']}"] = seed_deck['viewer_email']

        resp = client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 1,
            'comment': 'x' * 1000
        })
        assert resp.status_code == 200
        assert resp.get_json()['ok'] is True

    def test_comment_with_special_chars(self, client, seed_deck):
        """Comments with HTML/special chars should be stored as-is."""
        with client.session_transaction() as sess:
            sess[f"viewer_email_{seed_deck['token']}"] = seed_deck['viewer_email']

        comment = '<script>alert("xss")</script> & "quotes" \'apostrophes\''
        resp = client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 2,
            'comment': comment
        })
        assert resp.status_code == 200
        assert resp.get_json()['ok'] is True

    def test_comment_with_unicode(self, client, seed_deck):
        with client.session_transaction() as sess:
            sess[f"viewer_email_{seed_deck['token']}"] = seed_deck['viewer_email']

        resp = client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 3,
            'comment': 'Great slide! \U0001f44d \u2014 very insightful'
        })
        assert resp.status_code == 200
        assert resp.get_json()['ok'] is True


class TestGetAllFeedbackValidation:
    """GET /api/feedback/all — input validation."""

    def test_missing_view_id_param(self, client):
        resp = client.get('/api/feedback/all')
        assert resp.status_code == 400

    def test_nonexistent_view_id(self, client):
        resp = client.get('/api/feedback/all?view_id=999999')
        assert resp.status_code == 404

    def test_no_session_returns_403(self, client, seed_deck):
        resp = client.get(f'/api/feedback/all?view_id={seed_deck["view_id"]}')
        assert resp.status_code == 403

    def test_valid_session_returns_200(self, client, seed_deck):
        with client.session_transaction() as sess:
            sess[f"viewer_email_{seed_deck['token']}"] = seed_deck['viewer_email']

        resp = client.get(f'/api/feedback/all?view_id={seed_deck["view_id"]}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ok'] is True
        assert 'feedback' in data
