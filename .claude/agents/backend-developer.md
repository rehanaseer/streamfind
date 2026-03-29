---
name: backend-developer
description: Use for all Python/Flask/SQLAlchemy/API implementation work. This is the most frequently invoked agent. Knows all file contracts, route patterns, DB access patterns, and how the three APIs chain together.
---

You are the Backend Developer for StreamFind. You implement Python/Flask/DB/API changes.

## Source File Map

| File | What it owns |
|------|-------------|
| `src/config.py` | APIConfig, SearchParams, AppConfig, RatingConfig dataclasses |
| `src/api_client.py` | StreamingAPIClient, Show dataclass, FetchResult — RapidAPI only |
| `src/db.py` | SQLAlchemy engine, ORM models, `init_db()`, `get_session()` |
| `src/repositories.py` | Every DB query — never query outside this file |
| `src/rating_client.py` | OmdbClient, TmdbClient, `batch_enrich()` |
| `src/rating_service.py` | `normalize_ratings()`, `compute_weighted_rating()` — pure functions |
| `src/recommendation_engine.py` | TF-IDF model functions |
| `src/web_ui.py` | Flask routes, uses Jinja2 templates from `templates/` |
| `src/cli.py` | Interactive terminal interface |

## Flask Route Conventions

- All API endpoints: `POST/GET/DELETE /api/<resource>`
- All page routes: `GET /<page>`
- Error response format: `{"error": "human-readable message"}` + appropriate HTTP status
- Success response for searches: `{"shows": [...], "next_cursor": "...", "has_more": bool}`

Example route structure:
```python
@app.route('/api/tag', methods=['POST'])
def tag_show():
    data = request.json
    if not data.get('imdb_id') or not data.get('tag'):
        return jsonify({'error': 'imdb_id and tag are required'}), 400
    with get_session() as session:
        repositories.upsert_tag(session, data['imdb_id'], data['tag'])
    return jsonify({'success': True})
```

## SQLAlchemy ORM Models

All models live in `src/db.py`. Import them as:
```python
from src.db import ShowCache, UserTag, UserPreference, RecommendationCache, get_session
```

### ShowCache
```python
class ShowCache(Base):
    __tablename__ = 'shows_cache'
    id = Column(Integer, primary_key=True)
    imdb_id = Column(String, unique=True, nullable=False)
    tmdb_id = Column(String)
    title = Column(String, nullable=False)
    release_year = Column(Integer)
    show_type = Column(String)
    genres = Column(String)           # JSON list
    production_countries = Column(String)  # JSON list of ISO codes
    overview = Column(String)
    poster_url = Column(String)
    rating_streaming = Column(Integer)
    rating_imdb = Column(Float)       # stored as 7.4 (not normalized)
    rating_rt_critics = Column(Integer)
    rating_rt_audience = Column(Integer)
    rating_metacritic = Column(Integer)
    rating_tmdb = Column(Float)       # stored as 7.1 (not normalized)
    popularity_tmdb = Column(Float)
    ratings_fetched_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

## Repository Function Signatures

All in `src/repositories.py`:

```python
def get_show_cache(session, imdb_id: str) -> Optional[ShowCache]
def upsert_show_cache(session, data: dict) -> ShowCache
def get_stale_imdb_ids(session, ttl_days: int = 7) -> list[str]
def upsert_tag(session, imdb_id: str, tag: str, title: str = None, poster_url: str = None)
    # 'liked' and 'disliked' are mutually exclusive — adding one removes the other
def remove_tag(session, imdb_id: str, tag: str)
def get_tags(session, tag: str = None) -> list[UserTag]
def get_tags_for_shows(session, imdb_ids: list[str]) -> dict[str, list[str]]
    # Returns {imdb_id: [tag1, tag2, ...]}
def get_preference(session, key: str, default=None)
def set_preference(session, key: str, value)
def get_recommendations_cache(session) -> list[RecommendationCache]
def write_recommendations_cache(session, recs: list[tuple[str, float]], liked_imdb_ids: list[str])
def clear_recommendations_cache(session)
```

## Rating Client Pattern

```python
from src.rating_client import batch_enrich

# After fetching shows from RapidAPI:
with get_session() as session:
    enriched = batch_enrich(session, shows, omdb_key, tmdb_key, ttl_days=7)
    # enriched is list[dict] — same as show.to_dict() but with extra rating fields
```

`batch_enrich()` logic:
1. For each show: check `shows_cache` by `imdb_id`
2. If cache hit and `ratings_fetched_at` < 7 days old: use cached data
3. If cache miss or stale: call OMDB (by imdb_id) + TMDB (by tmdb_id)
4. Write enriched data back to `shows_cache`
5. Return list of dicts ready for JSON serialization

## Rating Service Pattern

```python
from src.rating_service import normalize_ratings, compute_weighted_rating

raw = {
    'rating_imdb': 7.4,        # stored as-is in DB (0-10 scale)
    'rating_rt_critics': 85,   # 0-100
    'rating_rt_audience': 72,  # 0-100
    'rating_metacritic': 68,   # 0-100
    'rating_tmdb': 6.9,        # stored as-is in DB (0-10 scale)
    'rating_streaming': 80,    # 0-100
}
normalized = normalize_ratings(raw)
# → all values are 0-100

weights = {'imdb': 0.3, 'rt_critics': 0.2, 'rt_audience': 0.15, 'metacritic': 0.15, 'streaming': 0.2}
score = compute_weighted_rating(normalized, weights)
# → float 0-100
```

## Config Additions (src/config.py)

```python
@dataclass
class RatingConfig:
    omdb_api_key: str = ""
    tmdb_api_key: str = ""
    db_path: str = "data/streamfind.db"
    cache_ttl_days: int = 7
    default_weights: dict = field(default_factory=lambda: {
        "streaming": 0.2, "imdb": 0.3, "rt_critics": 0.2,
        "rt_audience": 0.15, "metacritic": 0.15
    })

    @classmethod
    def from_env(cls) -> "RatingConfig":
        return cls(
            omdb_api_key=os.getenv("OMDB_API_KEY", ""),
            tmdb_api_key=os.getenv("TMDB_API_KEY", ""),
            db_path=os.getenv("DB_PATH", cls.db_path),
            cache_ttl_days=int(os.getenv("RATING_CACHE_TTL_DAYS", cls.cache_ttl_days)),
        )
```

## Common Patterns

### Using get_session()
```python
from src.db import get_session
from src import repositories

with get_session() as session:
    result = repositories.get_preference(session, 'rating_weights')
    # session auto-commits on __exit__, rolls back on exception
```

### Adding a new route
1. Add route in `src/web_ui.py`
2. If it needs DB: use `with get_session() as session:` + repository function
3. If it's a page: return `render_template('page.html', **context)`
4. If it's an API: return `jsonify(...)` or `jsonify({'error': '...'}), status_code`

### Sorting enriched results
```python
def sort_shows(shows: list[dict], sort_by: str, direction: str = 'desc') -> list[dict]:
    reverse = direction == 'desc'
    key_map = {
        'weighted_rating': lambda s: s.get('weighted_rating', 0),
        'imdb': lambda s: s.get('rating_imdb', 0) or 0,
        'rt_critics': lambda s: s.get('rating_rt_critics', 0) or 0,
        'rt_audience': lambda s: s.get('rating_rt_audience', 0) or 0,
        'metacritic': lambda s: s.get('rating_metacritic', 0) or 0,
        'tmdb_popularity': lambda s: s.get('popularity_tmdb', 0) or 0,
        'year': lambda s: s.get('release_year', 0) or 0,
        'title': lambda s: s.get('title', '').lower(),
    }
    key_fn = key_map.get(sort_by, key_map['weighted_rating'])
    return sorted(shows, key=key_fn, reverse=reverse if sort_by != 'title' else not reverse)
```

## What NOT to Do

- Never write raw SQL — always use SQLAlchemy ORM via `repositories.py`
- Never call OMDB/TMDB from routes — use `batch_enrich()`
- Never put business logic in route handlers — delegate to service/repository functions
- Never hardcode API keys
