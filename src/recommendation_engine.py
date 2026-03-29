"""
ML Recommendation Engine for StreamFind.

Uses TF-IDF cosine similarity on show features (genres, production countries, decade).
Requires minimum 3 liked titles to produce recommendations.

All DB access happens OUTSIDE this module — receive data as arguments,
return results as plain dicts/lists.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


def build_feature_string(show) -> str:
    """
    Build a text feature string for a ShowCache row.
    Used as input to TF-IDF vectorizer.

    Format: "genre1 genre2 country1 country2 2010s"
    """
    parts = []

    # Genres (lowercased, spaces removed)
    try:
        genres = json.loads(show.genres) if isinstance(show.genres, str) else (show.genres or [])
        for g in genres:
            parts.append(g.lower().replace(' ', '_'))
    except (json.JSONDecodeError, TypeError):
        pass

    # Production countries
    try:
        countries = json.loads(show.production_countries) if isinstance(show.production_countries, str) else (show.production_countries or [])
        for c in countries:
            parts.append(f"country_{c.lower()}")
    except (json.JSONDecodeError, TypeError):
        pass

    # Decade
    if show.release_year:
        decade = (show.release_year // 10) * 10
        parts.append(f"{decade}s")

    return " ".join(parts) if parts else "unknown"


def train(all_shows: list) -> Optional[tuple]:
    """
    Fit a TF-IDF vectorizer on all known shows.

    Returns (vectorizer, matrix, imdb_id_index) or None if not enough shows.

    imdb_id_index: list of imdb_ids in the same order as matrix rows.
    """
    if not all_shows:
        return None

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np

        feature_strings = [build_feature_string(s) for s in all_shows]
        imdb_id_index = [s.imdb_id for s in all_shows]

        vectorizer = TfidfVectorizer(min_df=1, ngram_range=(1, 1))
        matrix = vectorizer.fit_transform(feature_strings)

        return vectorizer, matrix, imdb_id_index

    except Exception as e:
        logger.warning(f"TF-IDF training failed: {e}")
        return None


def recommend(
    liked_ids: list,
    disliked_ids: list,
    vectorizer,
    matrix,
    imdb_id_index: list,
    n: int = 20,
) -> list:
    """
    Generate recommendations from a trained TF-IDF model.

    Averages the feature vectors of liked shows, subtracts disliked influence,
    then returns the top-N most similar shows not already tagged.

    Returns list of (imdb_id, similarity_score) tuples.
    """
    if len(liked_ids) < 3:
        return []

    try:
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        # Build positive profile from liked shows
        liked_indices = [imdb_id_index.index(iid) for iid in liked_ids if iid in imdb_id_index]
        if not liked_indices:
            return []

        liked_matrix = matrix[liked_indices]
        profile = np.asarray(liked_matrix.mean(axis=0))

        # Subtract disliked influence (with 50% weight)
        disliked_indices = [imdb_id_index.index(iid) for iid in disliked_ids if iid in imdb_id_index]
        if disliked_indices:
            disliked_matrix = matrix[disliked_indices]
            disliked_profile = np.asarray(disliked_matrix.mean(axis=0))
            profile = profile - 0.5 * disliked_profile

        # Compute cosine similarity between profile and all shows
        scores = cosine_similarity(profile, matrix).flatten()

        # Build results, excluding already-tagged shows
        excluded = set(liked_ids) | set(disliked_ids)
        results = []
        for idx, score in enumerate(scores):
            imdb_id = imdb_id_index[idx]
            if imdb_id not in excluded and float(score) > 0:
                results.append((imdb_id, float(score)))

        # Sort by score descending, return top N
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:n]

    except Exception as e:
        logger.warning(f"Recommendation computation failed: {e}")
        return []


def get_or_rebuild_recommendations(session) -> list:
    """
    Return cached recommendations, rebuilding if stale or liked_count changed.

    Checks:
    1. Are there cached recommendations?
    2. Are they less than 24 hours old?
    3. Do they reflect the current liked count?

    If not, rebuilds and writes back to DB.

    Returns list of RecommendationCache rows.
    """
    from src import repositories
    from src.db import RecommendationCache

    liked_ids = repositories.get_liked_imdb_ids(session)

    if len(liked_ids) < 3:
        return []

    # Check if cache is fresh
    existing = repositories.get_recommendations_cache(session)
    if existing:
        oldest = existing[0].computed_at
        age_hours = (datetime.utcnow() - oldest).total_seconds() / 3600
        cached_based_on = json.loads(existing[0].based_on_tags) if existing[0].based_on_tags else []

        if age_hours < 24 and set(cached_based_on) == set(liked_ids):
            return existing

    # Rebuild
    all_shows = repositories.get_all_cached_shows(session)
    if not all_shows:
        return []

    model = train(all_shows)
    if model is None:
        return []

    vectorizer, matrix, imdb_id_index = model
    disliked_ids = repositories.get_disliked_imdb_ids(session)

    raw_recs = recommend(liked_ids, disliked_ids, vectorizer, matrix, imdb_id_index, n=20)

    if not raw_recs:
        return []

    # Enrich with title/poster from cache
    recs_with_meta = []
    for imdb_id, score in raw_recs:
        cache_row = repositories.get_show_cache(session, imdb_id)
        title = cache_row.title if cache_row else None
        poster = cache_row.poster_url if cache_row else None
        recs_with_meta.append((imdb_id, score, title, poster))

    repositories.write_recommendations_cache(session, recs_with_meta, liked_ids)
    session.flush()

    return repositories.get_recommendations_cache(session)
