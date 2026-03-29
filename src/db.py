"""
Database module for StreamFind.

Owns SQLAlchemy engine, ORM models, init_db(), and get_session().
All other modules interact with the DB through repositories.py.
"""

import os
import json
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Text, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()

_engine = None
_SessionFactory = None


def _get_db_url() -> str:
    db_path = os.getenv("DB_PATH", "data/streamfind.db")
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    return f"sqlite:///{db_path}"


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_get_db_url(), connect_args={"check_same_thread": False})
    return _engine


def init_db(engine=None) -> None:
    """Create all tables and seed default preferences."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)

    # Seed default preferences
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        _seed_defaults(session)
        session.commit()
    finally:
        session.close()


def _seed_defaults(session: Session) -> None:
    """Insert default user_preferences rows if they don't exist."""
    defaults = {
        "rating_weights": {
            "streaming": 0.1,
            "imdb": 0.25,
            "rt_critics": 0.2,
            "rt_audience": 0.2,
            "metacritic": 0.15,
            "tmdb": 0.1,
        },
        "visible_ratings": ["imdb", "rt_critics", "rt_audience", "metacritic", "tmdb"],
        "default_sort": "weighted_rating",
        "default_country": "ca",
    }
    for key, value in defaults.items():
        existing = session.query(UserPreference).filter_by(key=key).first()
        if not existing:
            session.add(UserPreference(key=key, value=json.dumps(value)))


@contextmanager
def get_session():
    """Context manager that yields a SQLAlchemy session, commits on success."""
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())

    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ─── ORM Models ──────────────────────────────────────────────────────────────

class ShowCache(Base):
    """Cached enriched show data with multi-source ratings. TTL = 7 days."""
    __tablename__ = "shows_cache"

    id = Column(Integer, primary_key=True)
    imdb_id = Column(String, unique=True, nullable=False)
    tmdb_id = Column(String)
    title = Column(String, nullable=False)
    release_year = Column(Integer)
    show_type = Column(String)           # 'movie' or 'series'
    genres = Column(Text)                # JSON: ["Horror","Drama"]
    production_countries = Column(Text)  # JSON: ["US","GB"]
    overview = Column(Text)
    poster_url = Column(String)

    # Ratings — stored in their natural scale (IMDB/TMDB as 0-10, others as 0-100)
    rating_streaming = Column(Integer)   # 0-100 from Streaming Availability API
    rating_imdb = Column(Float)          # 0-10 scale (e.g. 7.4)
    rating_rt_critics = Column(Integer)  # 0-100
    rating_rt_audience = Column(Integer) # 0-100
    rating_metacritic = Column(Integer)  # 0-100
    rating_tmdb = Column(Float)          # 0-10 scale (e.g. 7.1)
    popularity_tmdb = Column(Float)

    ratings_fetched_at = Column(DateTime)  # for TTL check
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def genres_list(self) -> list:
        return json.loads(self.genres) if self.genres else []

    def countries_list(self) -> list:
        return json.loads(self.production_countries) if self.production_countries else []


class UserTag(Base):
    """User's liked/disliked/watchlist tags for shows."""
    __tablename__ = "user_tags"
    __table_args__ = (UniqueConstraint("imdb_id", "tag"),)

    id = Column(Integer, primary_key=True)
    imdb_id = Column(String, nullable=False)
    tag = Column(String, nullable=False)   # 'liked', 'disliked', 'watchlist'
    title = Column(String)
    poster_url = Column(String)
    tagged_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)


class UserPreference(Base):
    """Key-value store for user settings (rating weights, visible ratings, etc.)."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=False)   # JSON-encoded
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecommendationCache(Base):
    """Pre-computed ML recommendation scores."""
    __tablename__ = "recommendation_cache"

    id = Column(Integer, primary_key=True)
    imdb_id = Column(String, nullable=False)
    title = Column(String)
    poster_url = Column(String)
    similarity_score = Column(Float)
    based_on_tags = Column(Text)  # JSON: list of imdb_ids used to compute
    computed_at = Column(DateTime, default=datetime.utcnow)
