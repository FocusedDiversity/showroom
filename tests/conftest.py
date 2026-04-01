"""Shared fixtures for unit and integration tests."""
import os
import pytest
import psycopg
from psycopg.rows import dict_row

# Use the same DB as dev — tests run in transactions that get rolled back
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://showroom:showroom@localhost:5432/showroom')

os.environ['DATABASE_URL'] = DATABASE_URL
os.environ['SECRET_KEY'] = 'test-secret-key'

from app import app as flask_app


@pytest.fixture
def app():
    """Create a Flask app configured for testing."""
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    return flask_app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def db_conn():
    """Direct database connection for test setup/teardown."""
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=False)
    yield conn
    # Rollback any uncommitted transaction before closing
    try:
        conn.rollback()
    except Exception:
        pass
    conn.close()


@pytest.fixture
def seed_deck(db_conn):
    """Create a test deck, share link, and view. Returns dict with IDs."""
    cur = db_conn.cursor()

    # Use a unique token per test to avoid conflicts
    import secrets
    unique_suffix = secrets.token_hex(4)
    token = f'test-feedback-token-{unique_suffix}'
    slug = f'test-feedback-deck-{unique_suffix}'

    # Create deck
    cur.execute(
        "INSERT INTO decks (title, slug, description) VALUES (%s, %s, %s) RETURNING id",
        ('Test Feedback Deck', slug, 'A test deck')
    )
    deck_id = cur.fetchone()['id']

    # Create share link
    cur.execute(
        "INSERT INTO share_links (deck_id, recipient_email, token) VALUES (%s, %s, %s) RETURNING id",
        (deck_id, 'recipient@test.com', token)
    )
    link_id = cur.fetchone()['id']

    # Create view
    cur.execute(
        "INSERT INTO views (share_link_id, viewer_email, user_agent, ip_address, is_forwarded) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (link_id, 'recipient@test.com', 'TestAgent/1.0', '127.0.0.1', False)
    )
    view_id = cur.fetchone()['id']

    db_conn.commit()

    data = {
        'deck_id': deck_id,
        'link_id': link_id,
        'view_id': view_id,
        'token': token,
        'viewer_email': 'recipient@test.com',
    }

    yield data

    # Cleanup
    cur.execute("DELETE FROM decks WHERE id = %s", (deck_id,))
    db_conn.commit()
