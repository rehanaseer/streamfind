# StreamFind — Claude Code Project Guide

StreamFind finds top-rated movies and TV shows across streaming platforms, enriching results with multi-source ratings (IMDB, Rotten Tomatoes, Metacritic, TMDB), weighted scoring, and ML-based personalized recommendations driven by the user's liked/disliked tags.

## Architecture

```
Browser
  │
  ▼
Flask (src/web_ui.py)
  │
  ├── Streaming Availability API (RapidAPI) ──► show list + streaming options
  ├── OMDB API ──────────────────────────────► IMDB, RT critics/audience, Metacritic
  ├── TMDB API ──────────────────────────────► TMDB score, popularity, production countries
  │
  └── SQLite (data/streamfind.db)
        ├── shows_cache      (enriched show data, 7-day TTL)
        ├── user_tags        (liked / disliked / watchlist)
        ├── user_preferences (rating weights, visible ratings, defaults)
        └── recommendation_cache (pre-computed ML recs)
```

## Tech Stack

- Python 3.12, Flask, Jinja2 templates
- SQLAlchemy ORM + SQLite (file: `data/streamfind.db`)
- scikit-learn (TF-IDF cosine similarity for ML recommendations)
- requests (HTTP calls to all 3 APIs)

## Required API Keys (in .env)

```
RAPID_API_KEY=...     # Streaming Availability API (RapidAPI) — already configured
OMDB_API_KEY=...      # https://www.omdbapi.com/apikey.aspx (free: 1000 req/day)
TMDB_API_KEY=...      # https://www.themoviedb.org/settings/api (free)
```

## File Map

| File | Responsibility |
|------|----------------|
| `main.py` | Entry point: CLI args, --init-db, launches Flask or CLI |
| `src/config.py` | All config dataclasses: APIConfig, SearchParams, AppConfig, RatingConfig |
| `src/api_client.py` | StreamingAPIClient: fetches shows from RapidAPI, pagination |
| `src/db.py` | SQLAlchemy engine, ORM models (ShowCache, UserTag, UserPreference, RecommendationCache), init_db(), get_session() |
| `src/repositories.py` | ALL database access — every query lives here, nowhere else |
| `src/rating_client.py` | OmdbClient, TmdbClient, batch_enrich() — checks cache first |
| `src/rating_service.py` | normalize_ratings(), compute_weighted_rating() — pure functions |
| `src/recommendation_engine.py` | TF-IDF model: build_feature_string(), train(), recommend(), get_or_rebuild_recommendations() |
| `src/web_ui.py` | Flask app: all routes, uses Jinja2 templates from templates/ |
| `src/cli.py` | Interactive terminal interface |
| `templates/base.html` | Base layout: nav, filter bar, CSS/JS imports |
| `templates/index.html` | Search results grid |
| `templates/watchlist.html` | Watchlist view |
| `templates/recommendations.html` | ML recommendations view |
| `static/css/main.css` | All base styles (extracted from original web_ui.py) |
| `static/css/tags.css` | Tag badge and icon button styles |
| `static/js/search.js` | Search, pagination, card rendering |
| `static/js/ratings.js` | Weight sliders, visible-rating toggles |
| `static/js/tags.js` | Tag buttons: optimistic UI, POST/DELETE /api/tag |
| `static/js/sort.js` | Client-side sort helpers |

## Critical Rules

1. **Never put DB queries outside `repositories.py`** — routes call repository functions only
2. **Never call OMDB/TMDB from Flask routes** — use `rating_client.batch_enrich()`
3. **Never put ML logic outside `recommendation_engine.py`**
4. **Never store API keys in code** — env vars only
5. **Preserve `/api/search` response contract**: `{shows, next_cursor, has_more}`
6. **All API routes under `/api/`** — page routes at top-level `/`
7. **Error responses**: always `{"error": "message"}` JSON with appropriate HTTP status

## Database

Initialize: `python main.py --init-db`

| Table | Purpose |
|-------|---------|
| `shows_cache` | Enriched show data cached for 7 days (keyed by imdb_id) |
| `user_tags` | User's liked/disliked/watchlist tags per show |
| `user_preferences` | Key-value store: rating weights, visible ratings, defaults |
| `recommendation_cache` | Pre-computed ML recommendations with similarity scores |

Default preference seeds (set at init_db time):
- `rating_weights`: `{"streaming": 0.2, "imdb": 0.3, "rt_critics": 0.2, "rt_audience": 0.15, "metacritic": 0.15}`
- `visible_ratings`: `["imdb", "rt_critics", "rt_audience", "metacritic"]`
- `default_sort`: `"weighted_rating"`

## Weighted Rating Formula

```
weighted = Σ(weight_i × normalized_score_i) / Σ(weight_i)
```

Normalization before weighting:
- IMDB: `rating × 10`  (0–10 scale → 0–100)
- TMDB: `vote_average × 10`  (0–10 scale → 0–100)
- RT critics, RT audience, Metacritic: already 0–100

## Tag Rules

- `liked` and `disliked` are **mutually exclusive** — adding one removes the other for the same show
- `watchlist` is **independent** of liked/disliked
- **Minimum 3 liked titles** required before recommendations are generated
- Recommendations rebuild automatically when liked/disliked count changes

## Running Locally

```bash
python main.py --init-db    # Initialize database (run once)
python main.py              # Web UI at http://localhost:5000
python main.py --cli        # Interactive CLI
python -m pytest tests/ -v  # Run tests
```

## Running with Docker

```bash
docker-compose up           # Web at http://localhost:8080
docker-compose --profile dev up  # Dev mode with hot reload
```

The `data/` directory is mounted as a volume so the SQLite database persists across container restarts.

## Available Agents

| Agent | Use for |
|-------|---------|
| `.claude/agents/solution-architect.md` | System design decisions, new systems, DB schema changes |
| `.claude/agents/backend-developer.md` | Python/Flask/DB/API implementation |
| `.claude/agents/frontend-developer.md` | HTML/CSS/JS, templates, UI components |
| `.claude/agents/product-owner.md` | Feature requirements, acceptance criteria, scope decisions |
| `.claude/agents/qa-engineer.md` | Writing tests, regression checks, test patterns |

## Feature Status

### Phase 1 — Foundation
- [ ] SQLite + SQLAlchemy persistence (`src/db.py`, `src/repositories.py`)
- [ ] OMDB + TMDB rating enrichment (`src/rating_client.py`)
- [ ] Weighted rating computation (`src/rating_service.py`)
- [ ] Production country filter
- [ ] Advanced sort (weighted_rating, imdb, rt_critics, rt_audience, metacritic, tmdb_popularity)
- [ ] Rating chips UI + weight sliders
- [ ] Templates extracted to `templates/` + `static/`

### Phase 2 — Tag System
- [ ] Like / dislike / watchlist tags
- [ ] Watchlist page
- [ ] Tag UI on cards

### Phase 3 — ML Recommendations
- [ ] TF-IDF content-based recommendations (`src/recommendation_engine.py`)
- [ ] Recommendations page

## Multi-User Migration Path

When multi-user profiles are needed:
1. Add `users` table: `id, username, email, created_at`
2. Add `user_id` FK to `user_tags` and `user_preferences`
3. Add session/auth middleware
4. Scope all repository functions to accept `user_id` param

The ORM makes this a one-migration change. No other architectural changes needed.

## What NOT to Do

- Do not add raw SQL — always use SQLAlchemy via `repositories.py`
- Do not call OMDB/TMDB APIs directly from routes — use `rating_client.batch_enrich()`
- Do not break the `/api/search` response contract (`shows`, `next_cursor`, `has_more`)
- Do not add features, refactors, or comments beyond what is asked
- Do not hardcode API keys — environment variables only
- Do not add `user_id` columns yet — single-user for now, multi-user migration is documented above
