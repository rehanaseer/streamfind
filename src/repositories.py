"""
Data access layer for StreamFind.

ALL database queries live here. No other file should query the DB directly.
"""

import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from .db import ShowCache, UserTag, UserPreference, RecommendationCache


# ─── Show Cache ───────────────────────────────────────────────────────────────

def get_show_cache(session: Session, imdb_id: str) -> Optional[ShowCache]:
    """Return cached show by imdb_id, or None if not found."""
    return session.query(ShowCache).filter_by(imdb_id=imdb_id).first()


def upsert_show_cache(session: Session, data: dict) -> ShowCache:
    """Insert or update a show in the cache. data must include 'imdb_id'."""
    row = session.query(ShowCache).filter_by(imdb_id=data["imdb_id"]).first()
    if row is None:
        row = ShowCache(imdb_id=data["imdb_id"])
        session.add(row)

    for field, value in data.items():
        if field in ("genres", "production_countries") and isinstance(value, list):
            value = json.dumps(value)
        if hasattr(row, field):
            setattr(row, field, value)

    row.updated_at = datetime.utcnow()
    session.flush()
    return row


def get_stale_imdb_ids(session: Session, ttl_days: int = 7) -> list:
    """Return imdb_ids whose ratings are older than ttl_days or never fetched."""
    cutoff = datetime.utcnow() - timedelta(days=ttl_days)
    rows = session.query(ShowCache.imdb_id).filter(
        (ShowCache.ratings_fetched_at == None) |  # noqa: E711
        (ShowCache.ratings_fetched_at < cutoff)
    ).all()
    return [r.imdb_id for r in rows]


def get_all_cached_shows(session: Session) -> list:
    """Return all ShowCache rows (used by recommendation engine)."""
    return session.query(ShowCache).all()


# ─── Tags ─────────────────────────────────────────────────────────────────────

def upsert_tag(session: Session, imdb_id: str, tag: str,
               title: str = None, poster_url: str = None) -> None:
    """
    Add a tag for a show.
    'liked' and 'disliked' are mutually exclusive — adding one removes the other.
    'watchlist' is independent.
    """
    if tag in ("liked", "disliked"):
        opposite = "disliked" if tag == "liked" else "liked"
        session.query(UserTag).filter_by(imdb_id=imdb_id, tag=opposite).delete()

    existing = session.query(UserTag).filter_by(imdb_id=imdb_id, tag=tag).first()
    if existing is None:
        row = UserTag(
            imdb_id=imdb_id,
            tag=tag,
            title=title,
            poster_url=poster_url,
        )
        session.add(row)
    else:
        if title:
            existing.title = title
        if poster_url:
            existing.poster_url = poster_url
    session.flush()


def remove_tag(session: Session, imdb_id: str, tag: str) -> None:
    """Remove a specific tag for a show."""
    session.query(UserTag).filter_by(imdb_id=imdb_id, tag=tag).delete()
    session.flush()


def get_tags(session: Session, tag: str = None) -> list:
    """Return all UserTag rows, optionally filtered by tag type."""
    query = session.query(UserTag)
    if tag:
        query = query.filter_by(tag=tag)
    return query.order_by(UserTag.tagged_at.desc()).all()


def get_tags_for_shows(session: Session, imdb_ids: list) -> dict:
    """Return {imdb_id: [tag1, tag2, ...]} for the given imdb_ids."""
    if not imdb_ids:
        return {}
    rows = session.query(UserTag).filter(UserTag.imdb_id.in_(imdb_ids)).all()
    result = {}
    for row in rows:
        result.setdefault(row.imdb_id, []).append(row.tag)
    return result


def get_liked_imdb_ids(session: Session) -> list:
    """Return list of imdb_ids tagged as 'liked'."""
    rows = session.query(UserTag.imdb_id).filter_by(tag="liked").all()
    return [r.imdb_id for r in rows]


def get_disliked_imdb_ids(session: Session) -> list:
    """Return list of imdb_ids tagged as 'disliked'."""
    rows = session.query(UserTag.imdb_id).filter_by(tag="disliked").all()
    return [r.imdb_id for r in rows]


# ─── Preferences ──────────────────────────────────────────────────────────────

def get_preference(session: Session, key: str, default=None):
    """Return a preference value (decoded from JSON), or default if not set."""
    row = session.query(UserPreference).filter_by(key=key).first()
    if row is None:
        return default
    return json.loads(row.value)


def set_preference(session: Session, key: str, value) -> None:
    """Set a preference value (encoded as JSON)."""
    row = session.query(UserPreference).filter_by(key=key).first()
    if row is None:
        session.add(UserPreference(key=key, value=json.dumps(value)))
    else:
        row.value = json.dumps(value)
        row.updated_at = datetime.utcnow()
    session.flush()


def seed_default_preferences(session: Session) -> None:
    """Seed default preferences if they don't exist (used by tests)."""
    defaults = {
        "rating_weights": {
            "streaming": 0.2, "imdb": 0.3, "rt_critics": 0.2,
            "rt_audience": 0.15, "metacritic": 0.15,
        },
        "visible_ratings": ["imdb", "rt_critics", "rt_audience", "metacritic"],
        "default_sort": "weighted_rating",
        "default_country": "ca",
    }
    for key, value in defaults.items():
        existing = session.query(UserPreference).filter_by(key=key).first()
        if not existing:
            session.add(UserPreference(key=key, value=json.dumps(value)))
    session.flush()


# ─── Recommendation Cache ─────────────────────────────────────────────────────

def get_recommendations_cache(session: Session) -> list:
    """Return all cached recommendation rows ordered by score."""
    return session.query(RecommendationCache).order_by(
        RecommendationCache.similarity_score.desc()
    ).all()


def write_recommendations_cache(session: Session,
                                 recs: list,
                                 liked_imdb_ids: list) -> None:
    """
    Replace recommendation cache with new results.
    recs: list of (imdb_id, score, title, poster_url)
    """
    session.query(RecommendationCache).delete()
    based_on = json.dumps(liked_imdb_ids)
    now = datetime.utcnow()
    for imdb_id, score, title, poster_url in recs:
        session.add(RecommendationCache(
            imdb_id=imdb_id,
            title=title,
            poster_url=poster_url,
            similarity_score=score,
            based_on_tags=based_on,
            computed_at=now,
        ))
    session.flush()


def clear_recommendations_cache(session: Session) -> None:
    """Clear all recommendation cache rows."""
    session.query(RecommendationCache).delete()
    session.flush()
