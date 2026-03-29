"""
Flask route integration tests.
Mocks StreamingAPIClient so no real HTTP calls are made.
"""

import pytest
from unittest.mock import patch, MagicMock

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client():
    from src.web_ui import app
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def _fake_show(title='Test Movie', imdb_id='tt1234567'):
    from src.api_client import Show
    return Show(
        title=title,
        release_year=2020,
        imdb_id=imdb_id,
        tmdb_id='12345',
        show_type='movie',
        rating=80,
        overview='A test movie.',
        genres=['Horror'],
        streaming_services=[{'name': 'Netflix', 'id': 'netflix', 'link': '', 'type': 'subscription', 'quality': 'hd'}],
        poster_url=None,
        raw_data={},
    )


# ── /api/search contract ──────────────────────────────

def test_filter_search_returns_contract(client):
    """/api/search (no title) must always return {shows, next_cursor, has_more}."""
    with patch('src.web_ui.StreamingAPIClient') as MockClient:
        MockClient.return_value.fetch_single_page.return_value = ([], None, False)
        res = client.post('/api/search', json={'country': 'ca', 'show_type': 'movie', 'genres': 'horror'})
        data = res.get_json()
        assert res.status_code == 200
        assert 'shows' in data
        assert 'next_cursor' in data
        assert 'has_more' in data


def test_title_search_returns_contract(client):
    """/api/search with title must return {shows, next_cursor, has_more}."""
    with patch('src.web_ui.StreamingAPIClient') as MockClient:
        MockClient.return_value.search_by_title.return_value = []
        res = client.post('/api/search', json={'title': 'Inception', 'country': 'ca'})
        data = res.get_json()
        assert res.status_code == 200
        assert 'shows' in data
        assert 'next_cursor' in data
        assert 'has_more' in data


def test_title_search_calls_search_by_title_not_fetch(client):
    """When title is provided, search_by_title is used; fetch_single_page is not called."""
    with patch('src.web_ui.StreamingAPIClient') as MockClient:
        instance = MockClient.return_value
        instance.search_by_title.return_value = []
        client.post('/api/search', json={'title': 'Inception', 'country': 'ca'})
        instance.search_by_title.assert_called_once()
        instance.fetch_single_page.assert_not_called()


def test_filter_search_does_not_call_search_by_title(client):
    """When title is absent, fetch_single_page is used; search_by_title is not called."""
    with patch('src.web_ui.StreamingAPIClient') as MockClient:
        instance = MockClient.return_value
        instance.fetch_single_page.return_value = ([], None, False)
        client.post('/api/search', json={'country': 'ca', 'genres': 'horror'})
        instance.fetch_single_page.assert_called()
        instance.search_by_title.assert_not_called()


def test_title_search_has_more_is_false(client):
    """Title search has no pagination — has_more must always be False."""
    with patch('src.web_ui.StreamingAPIClient') as MockClient:
        MockClient.return_value.search_by_title.return_value = [_fake_show()]
        res = client.post('/api/search', json={'title': 'Test', 'country': 'ca'})
        data = res.get_json()
        assert data['has_more'] is False
        assert data['next_cursor'] is None


def test_missing_api_key_returns_error(client):
    """Missing RAPID_API_KEY must return an error JSON."""
    with patch.dict('os.environ', {'RAPID_API_KEY': ''}):
        res = client.post('/api/search', json={})
        assert res.status_code == 500
        assert res.get_json().get('error') is not None


def test_empty_title_string_uses_filter_search(client):
    """An empty title string should fall through to filter search."""
    with patch('src.web_ui.StreamingAPIClient') as MockClient:
        instance = MockClient.return_value
        instance.fetch_single_page.return_value = ([], None, False)
        client.post('/api/search', json={'title': '  ', 'country': 'ca', 'genres': 'horror'})
        instance.fetch_single_page.assert_called()
        instance.search_by_title.assert_not_called()
