"""Integration tests for the slide feedback feature.

These tests hit the real PostgreSQL database and verify the full
request lifecycle: submit feedback, retrieve it, and see it in analytics.
"""
import pytest


class TestFeedbackSubmitAndRetrieve:
    """Full lifecycle: submit feedback via POST, retrieve via GET."""

    def _auth_session(self, client, seed_deck):
        with client.session_transaction() as sess:
            sess[f"viewer_email_{seed_deck['token']}"] = seed_deck['viewer_email']

    def test_submit_and_retrieve_single_feedback(self, client, seed_deck):
        self._auth_session(client, seed_deck)

        # Submit
        resp = client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 3,
            'comment': 'This slide is great!'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ok'] is True
        assert 'feedback_id' in data
        feedback_id = data['feedback_id']

        # Retrieve
        resp = client.get(f'/api/feedback?view_id={seed_deck["view_id"]}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ok'] is True
        assert len(data['feedback']) >= 1

        found = [f for f in data['feedback'] if f['id'] == feedback_id]
        assert len(found) == 1
        assert found[0]['slide_number'] == 3
        assert found[0]['comment'] == 'This slide is great!'
        assert 'created_at' in found[0]

    def test_multiple_feedback_same_slide(self, client, seed_deck):
        """Can submit multiple comments on the same slide."""
        self._auth_session(client, seed_deck)

        comments = ['First thought', 'Second thought', 'Third thought']
        for comment in comments:
            resp = client.post('/api/feedback', json={
                'view_id': seed_deck['view_id'],
                'slide_number': 5,
                'comment': comment
            })
            assert resp.status_code == 200

        resp = client.get(f'/api/feedback?view_id={seed_deck["view_id"]}')
        data = resp.get_json()
        slide_5 = [f for f in data['feedback'] if f['slide_number'] == 5]
        assert len(slide_5) == 3
        assert [f['comment'] for f in slide_5] == comments

    def test_feedback_across_different_slides(self, client, seed_deck):
        self._auth_session(client, seed_deck)

        for slide in [1, 4, 8]:
            resp = client.post('/api/feedback', json={
                'view_id': seed_deck['view_id'],
                'slide_number': slide,
                'comment': f'Comment on slide {slide}'
            })
            assert resp.status_code == 200

        resp = client.get(f'/api/feedback?view_id={seed_deck["view_id"]}')
        data = resp.get_json()
        slides = {f['slide_number'] for f in data['feedback']}
        assert {1, 4, 8}.issubset(slides)

    def test_feedback_ordered_by_created_at_asc(self, client, seed_deck):
        """Feedback should be returned oldest first."""
        self._auth_session(client, seed_deck)

        for i in range(3):
            client.post('/api/feedback', json={
                'view_id': seed_deck['view_id'],
                'slide_number': 1,
                'comment': f'Comment {i}'
            })

        resp = client.get(f'/api/feedback?view_id={seed_deck["view_id"]}')
        data = resp.get_json()
        slide_1 = [f for f in data['feedback'] if f['slide_number'] == 1]
        timestamps = [f['created_at'] for f in slide_1]
        assert timestamps == sorted(timestamps)


class TestAnalyticsWithFeedback:
    """Analytics API should include feedback data."""

    def _auth_session(self, client, seed_deck):
        with client.session_transaction() as sess:
            sess[f"viewer_email_{seed_deck['token']}"] = seed_deck['viewer_email']

    def test_analytics_includes_feedback(self, client, seed_deck):
        self._auth_session(client, seed_deck)

        # Submit some feedback
        client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 2,
            'comment': 'Analytics test feedback'
        })

        # Check analytics
        resp = client.get(f'/admin/api/analytics/{seed_deck["deck_id"]}')
        assert resp.status_code == 200
        data = resp.get_json()

        assert 'feedback' in data
        assert 'feedback_count' in data
        assert data['feedback_count'] >= 1

        found = [f for f in data['feedback'] if f['comment'] == 'Analytics test feedback']
        assert len(found) == 1
        assert found[0]['slide_number'] == 2
        assert found[0]['viewer_email'] == seed_deck['viewer_email']

    def test_analytics_feedback_empty_for_no_feedback(self, client, db_conn):
        """A deck with no feedback should return empty feedback array."""
        cur = db_conn.cursor()

        # Create a fresh deck with no feedback
        cur.execute(
            "INSERT INTO decks (title, slug, description) VALUES (%s, %s, %s) RETURNING id",
            ('No Feedback Deck', 'no-feedback-deck', '')
        )
        deck_id = cur.fetchone()['id']
        db_conn.commit()

        try:
            resp = client.get(f'/admin/api/analytics/{deck_id}')
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['feedback'] == []
            assert data['feedback_count'] == 0
        finally:
            cur.execute("DELETE FROM decks WHERE id = %s", (deck_id,))
            db_conn.commit()

    def test_analytics_feedback_has_correct_fields(self, client, seed_deck):
        self._auth_session(client, seed_deck)

        client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 7,
            'comment': 'Field check'
        })

        resp = client.get(f'/admin/api/analytics/{seed_deck["deck_id"]}')
        data = resp.get_json()
        fb = data['feedback'][0]

        assert 'id' in fb
        assert 'slide_number' in fb
        assert 'viewer_email' in fb
        assert 'comment' in fb
        assert 'created_at' in fb


class TestSharedFeedback:
    """GET /api/feedback/all — returns all feedback for the deck."""

    def _auth_session(self, client, token, email):
        with client.session_transaction() as sess:
            sess[f"viewer_email_{token}"] = email

    def test_all_feedback_returns_own_and_others(self, client, seed_deck, db_conn):
        """Should return feedback from both the current viewer and others."""
        # Viewer A submits feedback
        self._auth_session(client, seed_deck['token'], seed_deck['viewer_email'])
        client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 1,
            'comment': 'Viewer A comment'
        })

        # Create Viewer B and their feedback
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO views (share_link_id, viewer_email, user_agent, ip_address, is_forwarded) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (seed_deck['link_id'], 'viewerb@test.com', 'TestAgent', '127.0.0.1', True)
        )
        view_b_id = cur.fetchone()['id']
        cur.execute(
            "INSERT INTO slide_feedback (view_id, slide_number, comment) VALUES (%s, %s, %s)",
            (view_b_id, 1, 'Viewer B comment')
        )
        db_conn.commit()

        # Viewer A fetches all feedback
        resp = client.get(f'/api/feedback/all?view_id={seed_deck["view_id"]}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ok'] is True

        slide_1 = [f for f in data['feedback'] if f['slide_number'] == 1]
        assert len(slide_1) >= 2

        own = [f for f in slide_1 if f['is_own'] is True]
        others = [f for f in slide_1 if f['is_own'] is False]
        assert len(own) >= 1
        assert len(others) >= 1
        assert own[0]['viewer_email'] == 'You'

    def test_other_emails_are_obfuscated(self, client, seed_deck, db_conn):
        """Others' emails should be obfuscated (first char + *** + @domain)."""
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO views (share_link_id, viewer_email, user_agent, ip_address, is_forwarded) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (seed_deck['link_id'], 'sarah@acme.com', 'TestAgent', '127.0.0.1', True)
        )
        view_b_id = cur.fetchone()['id']
        cur.execute(
            "INSERT INTO slide_feedback (view_id, slide_number, comment) VALUES (%s, %s, %s)",
            (view_b_id, 2, 'Other feedback')
        )
        db_conn.commit()

        self._auth_session(client, seed_deck['token'], seed_deck['viewer_email'])
        resp = client.get(f'/api/feedback/all?view_id={seed_deck["view_id"]}')
        data = resp.get_json()

        other_items = [f for f in data['feedback'] if f['is_own'] is False]
        assert len(other_items) >= 1
        # Check obfuscation pattern
        email = other_items[0]['viewer_email']
        assert '***@' in email
        assert email.startswith('s***@acme.com')

    def test_all_feedback_ordered_by_created_at(self, client, seed_deck, db_conn):
        """Feedback should be ordered by created_at ascending."""
        self._auth_session(client, seed_deck['token'], seed_deck['viewer_email'])

        for i in range(3):
            client.post('/api/feedback', json={
                'view_id': seed_deck['view_id'],
                'slide_number': 1,
                'comment': f'Comment {i}'
            })

        resp = client.get(f'/api/feedback/all?view_id={seed_deck["view_id"]}')
        data = resp.get_json()
        timestamps = [f['created_at'] for f in data['feedback']]
        assert timestamps == sorted(timestamps)


class TestFeedbackIsolation:
    """Feedback should be scoped to the correct view/viewer."""

    def test_different_viewer_cannot_see_others_feedback(self, client, seed_deck, db_conn):
        """Viewer A's feedback should not be visible to Viewer B via GET /api/feedback."""
        # Viewer A submits feedback
        with client.session_transaction() as sess:
            sess[f"viewer_email_{seed_deck['token']}"] = seed_deck['viewer_email']

        client.post('/api/feedback', json={
            'view_id': seed_deck['view_id'],
            'slide_number': 1,
            'comment': 'Viewer A feedback'
        })

        # Create Viewer B's view
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO views (share_link_id, viewer_email, user_agent, ip_address, is_forwarded) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (seed_deck['link_id'], 'viewerb@test.com', 'TestAgent', '127.0.0.1', True)
        )
        view_b_id = cur.fetchone()['id']
        db_conn.commit()

        # Viewer B checks their feedback (should be empty)
        with client.session_transaction() as sess:
            sess[f"viewer_email_{seed_deck['token']}"] = 'viewerb@test.com'

        resp = client.get(f'/api/feedback?view_id={view_b_id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['feedback']) == 0


class TestFeedbackToggleAdmin:
    """Admin can create links with feedback enabled or disabled."""

    def test_create_link_with_feedback_enabled(self, client, seed_deck):
        resp = client.post(
            f'/admin/deck/{seed_deck["deck_id"]}/share',
            data={'email': 'fb-on@test.com', 'feedback_enabled': 'on'},
            follow_redirects=True
        )
        assert resp.status_code == 200
        assert b'fb-on@test.com' in resp.data

    def test_create_link_without_feedback(self, client, seed_deck):
        resp = client.post(
            f'/admin/deck/{seed_deck["deck_id"]}/share',
            data={'email': 'fb-off@test.com'},
            follow_redirects=True
        )
        assert resp.status_code == 200
        assert b'fb-off@test.com' in resp.data

    def test_feedback_enabled_defaults_true_in_db(self, db_conn, seed_deck):
        """The original seeded link should have feedback_enabled = TRUE."""
        cur = db_conn.cursor()
        row = cur.execute(
            "SELECT feedback_enabled FROM share_links WHERE id = %s",
            (seed_deck['link_id'],)
        ).fetchone()
        assert row['feedback_enabled'] is True

    def test_feedback_disabled_link_has_false(self, db_conn, seed_deck):
        """The no-feedback seeded link should have feedback_enabled = FALSE."""
        cur = db_conn.cursor()
        row = cur.execute(
            "SELECT feedback_enabled FROM share_links WHERE id = %s",
            (seed_deck['nofb_link_id'],)
        ).fetchone()
        assert row['feedback_enabled'] is False
