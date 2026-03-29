"""Tests for all repository (data access) functions."""

import pytest
from datetime import datetime, timedelta
from src import repositories


class TestShowCache:
    def test_upsert_creates_new_row(self, db_session):
        repositories.upsert_show_cache(db_session, {
            'imdb_id': 'tt001',
            'title': 'Test Movie',
            'release_year': 2021,
        })
        db_session.commit()
        row = repositories.get_show_cache(db_session, 'tt001')
        assert row is not None
        assert row.title == 'Test Movie'

    def test_upsert_updates_existing_row(self, db_session):
        repositories.upsert_show_cache(db_session, {'imdb_id': 'tt002', 'title': 'Old Title'})
        db_session.commit()
        repositories.upsert_show_cache(db_session, {'imdb_id': 'tt002', 'title': 'New Title'})
        db_session.commit()
        row = repositories.get_show_cache(db_session, 'tt002')
        assert row.title == 'New Title'

    def test_genres_list_serialized(self, db_session):
        repositories.upsert_show_cache(db_session, {
            'imdb_id': 'tt003',
            'title': 'Horror Film',
            'genres': ['Horror', 'Thriller'],
        })
        db_session.commit()
        row = repositories.get_show_cache(db_session, 'tt003')
        assert row.genres_list() == ['Horror', 'Thriller']

    def test_get_stale_ids_returns_never_fetched(self, db_session):
        repositories.upsert_show_cache(db_session, {'imdb_id': 'tt004', 'title': 'No Fetch'})
        db_session.commit()
        stale = repositories.get_stale_imdb_ids(db_session, ttl_days=7)
        assert 'tt004' in stale

    def test_get_stale_ids_excludes_fresh(self, db_session):
        repositories.upsert_show_cache(db_session, {
            'imdb_id': 'tt005',
            'title': 'Fresh',
            'ratings_fetched_at': datetime.utcnow(),
        })
        db_session.commit()
        stale = repositories.get_stale_imdb_ids(db_session, ttl_days=7)
        assert 'tt005' not in stale

    def test_get_stale_ids_includes_expired(self, db_session):
        repositories.upsert_show_cache(db_session, {
            'imdb_id': 'tt006',
            'title': 'Expired',
            'ratings_fetched_at': datetime.utcnow() - timedelta(days=8),
        })
        db_session.commit()
        stale = repositories.get_stale_imdb_ids(db_session, ttl_days=7)
        assert 'tt006' in stale


class TestTags:
    def test_upsert_tag_liked(self, db_session):
        repositories.upsert_tag(db_session, 'tt100', 'liked', 'A Movie', None)
        db_session.commit()
        tags = repositories.get_tags(db_session, 'liked')
        ids = [t.imdb_id for t in tags]
        assert 'tt100' in ids

    def test_liked_removes_disliked(self, db_session):
        repositories.upsert_tag(db_session, 'tt101', 'disliked')
        db_session.commit()
        repositories.upsert_tag(db_session, 'tt101', 'liked')
        db_session.commit()
        liked = [t.imdb_id for t in repositories.get_tags(db_session, 'liked')]
        disliked = [t.imdb_id for t in repositories.get_tags(db_session, 'disliked')]
        assert 'tt101' in liked
        assert 'tt101' not in disliked

    def test_disliked_removes_liked(self, db_session):
        repositories.upsert_tag(db_session, 'tt102', 'liked')
        db_session.commit()
        repositories.upsert_tag(db_session, 'tt102', 'disliked')
        db_session.commit()
        liked = [t.imdb_id for t in repositories.get_tags(db_session, 'liked')]
        disliked = [t.imdb_id for t in repositories.get_tags(db_session, 'disliked')]
        assert 'tt102' not in liked
        assert 'tt102' in disliked

    def test_watchlist_independent_of_liked(self, db_session):
        repositories.upsert_tag(db_session, 'tt103', 'liked')
        repositories.upsert_tag(db_session, 'tt103', 'watchlist')
        db_session.commit()
        liked = [t.imdb_id for t in repositories.get_tags(db_session, 'liked')]
        watchlist = [t.imdb_id for t in repositories.get_tags(db_session, 'watchlist')]
        assert 'tt103' in liked
        assert 'tt103' in watchlist

    def test_remove_tag(self, db_session):
        repositories.upsert_tag(db_session, 'tt104', 'watchlist')
        db_session.commit()
        repositories.remove_tag(db_session, 'tt104', 'watchlist')
        db_session.commit()
        watchlist = [t.imdb_id for t in repositories.get_tags(db_session, 'watchlist')]
        assert 'tt104' not in watchlist

    def test_get_tags_for_shows(self, db_session):
        repositories.upsert_tag(db_session, 'tt200', 'liked')
        repositories.upsert_tag(db_session, 'tt200', 'watchlist')
        repositories.upsert_tag(db_session, 'tt201', 'disliked')
        db_session.commit()
        result = repositories.get_tags_for_shows(db_session, ['tt200', 'tt201'])
        assert set(result['tt200']) == {'liked', 'watchlist'}
        assert result['tt201'] == ['disliked']


class TestPreferences:
    def test_get_default_rating_weights(self, db_session):
        weights = repositories.get_preference(db_session, 'rating_weights')
        assert weights is not None
        assert 'imdb' in weights

    def test_set_and_get_preference(self, db_session):
        repositories.set_preference(db_session, 'test_key', {'foo': 'bar'})
        db_session.commit()
        result = repositories.get_preference(db_session, 'test_key')
        assert result == {'foo': 'bar'}

    def test_missing_preference_returns_default(self, db_session):
        result = repositories.get_preference(db_session, 'nonexistent', default=42)
        assert result == 42

    def test_update_existing_preference(self, db_session):
        repositories.set_preference(db_session, 'rating_weights', {'imdb': 1.0})
        db_session.commit()
        result = repositories.get_preference(db_session, 'rating_weights')
        assert result['imdb'] == 1.0
