"""Tests for database initialization and ORM models."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.db import Base, ShowCache, UserTag, UserPreference, RecommendationCache, init_db


def test_init_db_creates_all_tables():
    engine = create_engine('sqlite:///:memory:')
    init_db(engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert 'shows_cache' in tables
    assert 'user_tags' in tables
    assert 'user_preferences' in tables
    assert 'recommendation_cache' in tables


def test_init_db_seeds_default_preferences():
    engine = create_engine('sqlite:///:memory:')
    init_db(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    prefs = {p.key: p for p in session.query(UserPreference).all()}
    assert 'rating_weights' in prefs
    assert 'visible_ratings' in prefs
    assert 'default_sort' in prefs
    session.close()


def test_show_cache_genres_list(db_session):
    import json
    show = ShowCache(imdb_id='tt999', title='Test', genres=json.dumps(['Horror', 'Drama']))
    db_session.add(show)
    db_session.commit()
    row = db_session.query(ShowCache).filter_by(imdb_id='tt999').first()
    assert row.genres_list() == ['Horror', 'Drama']


def test_show_cache_countries_list(db_session):
    import json
    show = ShowCache(imdb_id='tt998', title='Test', production_countries=json.dumps(['US', 'GB']))
    db_session.add(show)
    db_session.commit()
    row = db_session.query(ShowCache).filter_by(imdb_id='tt998').first()
    assert row.countries_list() == ['US', 'GB']


def test_user_tag_unique_constraint(db_session):
    from sqlalchemy.exc import IntegrityError
    db_session.add(UserTag(imdb_id='tt777', tag='liked'))
    db_session.commit()
    db_session.add(UserTag(imdb_id='tt777', tag='liked'))
    with pytest.raises(IntegrityError):
        db_session.commit()
