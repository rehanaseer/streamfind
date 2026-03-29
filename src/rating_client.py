"""
Rating enrichment client for StreamFind.

Priority order:
  1. MDBList  — primary: IMDB, RT Critics, RT Audience, Metacritic, TMDB, Trakt in one call
  2. OMDB     — fallback for any rating fields MDBList couldn't provide
  3. TMDB     — always called for production_countries + popularity (not in MDBList)

Do NOT call these from Flask routes directly — use batch_enrich().
"""

import requests
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from . import repositories
from .db import ShowCache


OMDB_BASE    = "https://www.omdbapi.com/"
TMDB_BASE    = "https://api.themoviedb.org/3"
MDBLIST_BASE = "https://mdblist.com/api/"


class MdblistClient:
    """
    Primary ratings source. One call returns IMDB, RT Critics, RT Audience,
    Metacritic, TMDB vote average, and Trakt score.

    MDBList source names → our fields:
      imdb             → rating_imdb         (0–10 scale)
      tomatoes         → rating_rt_critics   (0–100)
      tomatoesaudience → rating_rt_audience  (0–100)
      metacritic       → rating_metacritic   (0–100)
      tmdb             → rating_tmdb         (0–10, MDBList returns 0–100 so we divide by 10)
      trakt            → (ignored for now, no dedicated field)
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session = requests.Session()

    def get_ratings(self, imdb_id: str) -> dict:
        if not self.api_key or not imdb_id:
            return {}

        try:
            resp = self._session.get(
                MDBLIST_BASE,
                params={"apikey": self.api_key, "i": imdb_id},
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()

            if not data.get("response", True) or data.get("error"):
                return {}

            result = {}

            for entry in data.get("ratings", []):
                source = entry.get("source", "")
                value  = entry.get("value")
                if value is None or value == 0:
                    continue

                if source == "imdb":
                    result["rating_imdb"] = float(value)           # 0–10
                elif source == "tomatoes":
                    result["rating_rt_critics"] = int(value)       # 0–100
                elif source == "tomatoesaudience":
                    result["rating_rt_audience"] = int(value)      # 0–100
                elif source == "metacritic":
                    result["rating_metacritic"] = int(value)       # 0–100
                elif source == "tmdb":
                    # MDBList returns TMDB as 0–100; store as 0–10 to match raw TMDB scale
                    result["rating_tmdb"] = round(float(value) / 10, 2)

            return result

        except (requests.RequestException, ValueError, KeyError):
            return {}


class OmdbClient:
    """
    Fallback ratings source. Provides IMDB, RT Critics, Metacritic.
    Used only when MDBList is unavailable or missing specific fields.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session = requests.Session()

    def get_ratings(self, imdb_id: str) -> dict:
        if not self.api_key or not imdb_id:
            return {}

        try:
            resp = self._session.get(
                OMDB_BASE,
                params={"i": imdb_id, "apikey": self.api_key},
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("Response") == "False":
                return {}

            result = {}

            imdb_raw = data.get("imdbRating", "")
            if imdb_raw and imdb_raw != "N/A":
                try:
                    result["rating_imdb"] = float(imdb_raw)
                except ValueError:
                    pass

            for entry in data.get("Ratings", []):
                source = entry.get("Source", "")
                value  = entry.get("Value", "")

                if source == "Rotten Tomatoes" and value.endswith("%"):
                    try:
                        result["rating_rt_critics"] = int(value[:-1])
                    except ValueError:
                        pass

                elif source == "Metacritic" and "/100" in value:
                    try:
                        result["rating_metacritic"] = int(value.split("/")[0])
                    except ValueError:
                        pass

            return result

        except (requests.RequestException, ValueError):
            return {}


class TmdbClient:
    """
    Always called for production_countries and popularity.
    Also provides rating_tmdb as fallback.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session = requests.Session()

    def get_details(self, tmdb_id: str, show_type: str = "movie") -> dict:
        if not self.api_key or not tmdb_id:
            return {}

        # tmdb_id from Streaming Availability API comes as "movie/274" — strip the prefix
        clean_id   = tmdb_id.split("/")[-1] if "/" in tmdb_id else tmdb_id
        media_type = "movie" if show_type != "series" else "tv"
        url        = f"{TMDB_BASE}/{media_type}/{clean_id}"

        try:
            resp = self._session.get(url, params={"api_key": self.api_key}, timeout=8)
            resp.raise_for_status()
            data = resp.json()

            result = {}

            vote_avg = data.get("vote_average")
            if vote_avg is not None:
                result["rating_tmdb"] = float(vote_avg)            # 0–10

            popularity = data.get("popularity")
            if popularity is not None:
                result["popularity_tmdb"] = float(popularity)

            countries = data.get("production_countries", [])
            result["production_countries"] = [
                c.get("iso_3166_1", "") for c in countries if c.get("iso_3166_1")
            ]

            return result

        except (requests.RequestException, ValueError):
            return {}


def batch_enrich(
    session: Session,
    shows: list,
    mdblist_key: str = "",
    omdb_key: str = "",
    tmdb_key: str = "",
    ttl_days: int = 7,
) -> list:
    """
    Enrich a list of Show objects with multi-source ratings.

    For each show (identified by imdb_id):
    1. Check shows_cache — return cached data if fresh and has ratings
    2. Call MDBList (primary) — fills IMDB, RT Critics, RT Audience, Metacritic, TMDB
    3. Fill any still-missing rating fields from OMDB (fallback)
    4. Always call TMDB for production_countries + popularity
    5. Write merged result back to cache
    """
    mdblist = MdblistClient(mdblist_key)
    omdb    = OmdbClient(omdb_key)
    tmdb    = TmdbClient(tmdb_key)
    cutoff  = datetime.utcnow() - timedelta(days=ttl_days)

    enriched = []

    for show in shows:
        imdb_id = show.imdb_id
        if not imdb_id:
            enriched.append(_show_to_dict(show, cache_row=None))
            continue

        cache_row = repositories.get_show_cache(session, imdb_id)
        has_any_rating = cache_row is not None and any([
            cache_row.rating_imdb,
            cache_row.rating_rt_critics,
            cache_row.rating_metacritic,
            cache_row.rating_tmdb,
        ])
        has_countries = cache_row is not None and bool(cache_row.production_countries)
        is_fresh = (
            cache_row is not None
            and cache_row.ratings_fetched_at is not None
            and cache_row.ratings_fetched_at >= cutoff
            and has_any_rating
            and has_countries
        )

        if not is_fresh:
            # Step 1: MDBList (primary)
            ratings = mdblist.get_ratings(imdb_id)

            # Step 2: OMDB fallback for any missing rating fields
            needs_omdb = not all([
                ratings.get("rating_imdb"),
                ratings.get("rating_rt_critics"),
                ratings.get("rating_metacritic"),
            ])
            if needs_omdb:
                omdb_data = omdb.get_ratings(imdb_id)
                for field in ("rating_imdb", "rating_rt_critics", "rating_metacritic"):
                    if ratings.get(field) is None and omdb_data.get(field) is not None:
                        ratings[field] = omdb_data[field]

            # Step 3: TMDB for production_countries + popularity (+ rating fallback)
            tmdb_data = tmdb.get_details(show.tmdb_id or "", show.show_type)
            if ratings.get("rating_tmdb") is None and tmdb_data.get("rating_tmdb") is not None:
                ratings["rating_tmdb"] = tmdb_data["rating_tmdb"]

            update = {
                "imdb_id": imdb_id,
                "tmdb_id": show.tmdb_id,
                "title": show.title,
                "release_year": show.release_year,
                "show_type": show.show_type,
                "genres": show.genres,
                "overview": show.overview,
                "poster_url": show.poster_url,
                "rating_streaming": show.rating,
                "ratings_fetched_at": datetime.utcnow(),
                **ratings,
                "popularity_tmdb": tmdb_data.get("popularity_tmdb"),
                "production_countries": tmdb_data.get("production_countries", []),
            }

            cache_row = repositories.upsert_show_cache(session, update)
            session.flush()

        enriched.append(_show_to_dict(show, cache_row))

    return enriched


def _show_to_dict(show, cache_row: Optional[ShowCache]) -> dict:
    """Merge Show object and ShowCache row into a single dict for API response."""
    base = show.to_dict()

    if cache_row:
        base.update({
            "rating_imdb":       cache_row.rating_imdb,
            "rating_rt_critics": cache_row.rating_rt_critics,
            "rating_rt_audience":cache_row.rating_rt_audience,
            "rating_metacritic": cache_row.rating_metacritic,
            "rating_tmdb":       cache_row.rating_tmdb,
            "popularity_tmdb":   cache_row.popularity_tmdb,
            "production_countries": cache_row.countries_list(),
        })
    else:
        base.update({
            "rating_imdb":       None,
            "rating_rt_critics": None,
            "rating_rt_audience":None,
            "rating_metacritic": None,
            "rating_tmdb":       None,
            "popularity_tmdb":   None,
            "production_countries": [],
        })

    return base
