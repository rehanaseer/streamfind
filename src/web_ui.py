"""
Web UI for StreamFind.

Flask routes only — no business logic, no DB queries, no direct API calls.
All DB access via repositories.py, all rating enrichment via rating_client.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify
from src.config import APIConfig, SearchParams, AppConfig, RatingConfig
from src.api_client import StreamingAPIClient

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates"),
    static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"),
)
app.secret_key = os.urandom(24)


def get_config() -> AppConfig:
    return AppConfig.from_env()


def _get_watchlist_count() -> int:
    """Return watchlist count for nav badge, returns 0 on any error."""
    try:
        from src.db import get_session
        from src import repositories
        with get_session() as session:
            return len(repositories.get_tags(session, tag="watchlist"))
    except Exception:
        return 0


# ─── Page Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    config = get_config()
    defaults = SearchParams()
    return render_template(
        'index.html',
        active_page='search',
        watchlist_count=_get_watchlist_count(),
        config=config,
        countries=defaults.COUNTRIES,
        show_types=defaults.SHOW_TYPES,
        genres=defaults.GENRES,
        streaming_services=defaults.STREAMING_SERVICES,
        production_countries=defaults.PRODUCTION_COUNTRIES,
        order_options=defaults.ORDER_BY_OPTIONS,
        direction_options=defaults.ORDER_DIRECTION_OPTIONS,
    )


@app.route('/watchlist')
def watchlist():
    try:
        from src.db import get_session, init_db
        from src import repositories
        from src.rating_service import apply_weighted_rating
        init_db()
        with get_session() as session:
            weights = repositories.get_preference(
                session, 'rating_weights',
                default={'imdb': 0.3, 'rt_critics': 0.2, 'rt_audience': 0.15, 'metacritic': 0.15, 'streaming': 0.2}
            )
            tags = repositories.get_tags(session, tag='watchlist')
            imdb_ids = [t.imdb_id for t in tags]
            shows = []
            for tag in tags:
                cache = repositories.get_show_cache(session, tag.imdb_id)
                if cache:
                    show = {
                        'imdb_id': tag.imdb_id,
                        'title': cache.title,
                        'poster_url': cache.poster_url,
                        'release_year': cache.release_year,
                        'genres': cache.genres_list(),
                        'rating': cache.rating_streaming,
                        'rating_imdb': cache.rating_imdb,
                        'rating_rt_critics': cache.rating_rt_critics,
                        'rating_rt_audience': cache.rating_rt_audience,
                        'rating_metacritic': cache.rating_metacritic,
                        'rating_tmdb': cache.rating_tmdb,
                    }
                    apply_weighted_rating(show, weights)
                else:
                    show = {
                        'imdb_id': tag.imdb_id,
                        'title': tag.title or 'Unknown',
                        'poster_url': tag.poster_url,
                        'release_year': None,
                        'genres': [],
                        'rating': None,
                        'weighted_rating': None,
                    }
                shows.append(show)
    except Exception:
        shows = []

    return render_template(
        'watchlist.html',
        active_page='watchlist',
        watchlist_count=len(shows),
        shows=shows,
    )


@app.route('/recommendations')
def recommendations():
    try:
        from src.db import get_session, init_db
        from src import repositories
        from src.recommendation_engine import get_or_rebuild_recommendations
        init_db()
        with get_session() as session:
            liked_count = len(repositories.get_liked_imdb_ids(session))
            enough = liked_count >= 3

            if enough:
                recs = get_or_rebuild_recommendations(session)
                liked_tags = repositories.get_tags(session, tag='liked')
                liked_titles = [t.title for t in liked_tags if t.title]

                # Fetch full show data for each rec
                tag_map = repositories.get_tags_for_shows(
                    session, [r.imdb_id for r in recs]
                )
                shows = []
                for rec in recs[:20]:
                    cache = repositories.get_show_cache(session, rec.imdb_id)
                    if cache:
                        shows.append({
                            'imdb_id': rec.imdb_id,
                            'title': rec.title or cache.title,
                            'poster_url': rec.poster_url or cache.poster_url,
                            'release_year': cache.release_year,
                            'genres': cache.genres_list(),
                            'rating': cache.rating_streaming,
                            'similarity_score': rec.similarity_score,
                            'current_tags': tag_map.get(rec.imdb_id, []),
                        })
            else:
                shows = []
                liked_titles = []
    except Exception:
        shows = []
        liked_titles = []
        liked_count = 0
        enough = False

    return render_template(
        'recommendations.html',
        active_page='recommendations',
        watchlist_count=_get_watchlist_count(),
        shows=shows,
        liked_titles=liked_titles,
        liked_count=liked_count,
        enough_likes=enough,
    )


# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json or {}

    api_key = os.getenv('RAPID_API_KEY', '')
    if not api_key:
        return jsonify({'error': 'RAPID_API_KEY is not set in the server environment.'}), 500

    api_config = APIConfig(api_key=api_key)
    client = StreamingAPIClient(api_config)

    title_query = data.get('title', '').strip()
    production_country_filter = data.get('production_country', '')

    next_cursor = None
    has_more = False

    if title_query:
        # Title search — bypass filter params, return all matches
        try:
            shows = client.search_by_title(
                title=title_query,
                country=data.get('country', 'ca'),
                show_type=data.get('show_type', '') or '',
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        search_params = SearchParams(
            country=data.get('country', 'ca'),
            show_type=data.get('show_type', ''),
            genres=data.get('genres', ''),
            rating_min=str(data.get('rating_min', 70)),
            order_by='rating',  # always fetch by streaming rating; we re-sort client-side
            order_direction=data.get('order_direction', 'desc'),
            services=data.get('services', ''),
        )

        PAGE_SIZE = 18
        # When filtering by production country client-side, fetch more candidates
        # because the API sorts by streaming rating and non-English titles appear
        # further down the list. 10 pages gives a large enough pool.
        fetch_target = PAGE_SIZE * 10 if production_country_filter else PAGE_SIZE
        cursor = data.get('cursor') or None
        all_shows = []

        try:
            while len(all_shows) < fetch_target:
                page_shows, page_cursor, page_has_more = client.fetch_single_page(
                    search_params, cursor=cursor
                )
                all_shows.extend(page_shows)
                has_more = page_has_more
                next_cursor = page_cursor
                if not page_has_more or not page_cursor:
                    break
                cursor = page_cursor
        except Exception as e:
            return jsonify({'error': str(e)}), 500

        shows = all_shows

    # Attempt rating enrichment (fails gracefully if no API keys or DB)
    enriched = []
    try:
        from src.db import get_session, init_db
        from src import repositories
        from src.rating_client import batch_enrich
        from src.rating_service import apply_weighted_rating, sort_shows

        rating_config = RatingConfig.from_env()
        init_db()

        with get_session() as session:
            weights = repositories.get_preference(
                session, 'rating_weights',
                default={'imdb': 0.3, 'rt_critics': 0.2, 'rt_audience': 0.15, 'metacritic': 0.15, 'streaming': 0.2}
            )
            enriched = batch_enrich(
                session, shows,
                mdblist_key=rating_config.mdblist_api_key,
                omdb_key=rating_config.omdb_api_key,
                tmdb_key=rating_config.tmdb_api_key,
                ttl_days=rating_config.cache_ttl_days,
            )

            # Apply weighted rating
            for show_dict in enriched:
                apply_weighted_rating(show_dict, weights)

            # Apply production country filter
            if production_country_filter:
                enriched = [
                    s for s in enriched
                    if production_country_filter.upper() in [c.upper() for c in (s.get('production_countries') or [])]
                ]


            # Re-sort by user's chosen sort field
            sort_by = data.get('order_by', 'weighted_rating')
            direction = data.get('order_direction', 'desc')
            enriched = sort_shows(enriched, sort_by, direction)

            # Attach current tags
            imdb_ids = [s['imdb_id'] for s in enriched if s.get('imdb_id')]
            tag_map = repositories.get_tags_for_shows(session, imdb_ids)
            for show_dict in enriched:
                iid = show_dict.get('imdb_id')
                show_dict['current_tags'] = tag_map.get(iid, []) if iid else []

    except Exception:
        # Fall back to base show data without enrichment
        enriched = [s.to_dict() for s in shows]
        for s in enriched:
            s['current_tags'] = []

    return jsonify({
        'shows': enriched,
        'next_cursor': next_cursor,
        'has_more': has_more,
    })


@app.route('/api/test', methods=['POST'])
def test_connection():
    data = request.json or {}
    api_key = data.get('api_key', '')
    if not api_key:
        return jsonify({'success': False, 'message': 'API key required'}), 400
    api_config = APIConfig(api_key=api_key)
    client = StreamingAPIClient(api_config)
    success, message = client.test_connection()
    return jsonify({'success': success, 'message': message})


@app.route('/api/tag', methods=['POST'])
def add_tag():
    data = request.json or {}
    imdb_id = data.get('imdb_id', '').strip()
    tag = data.get('tag', '').strip()

    if not imdb_id or not tag:
        return jsonify({'error': 'imdb_id and tag are required'}), 400
    if tag not in ('liked', 'disliked', 'watchlist'):
        return jsonify({'error': 'tag must be liked, disliked, or watchlist'}), 400

    try:
        from src.db import get_session, init_db
        from src import repositories
        init_db()
        with get_session() as session:
            repositories.upsert_tag(
                session,
                imdb_id=imdb_id,
                tag=tag,
                title=data.get('title'),
                poster_url=data.get('poster_url'),
            )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'success': True})


@app.route('/api/tag/<imdb_id>/<tag>', methods=['DELETE'])
def remove_tag(imdb_id, tag):
    if tag not in ('liked', 'disliked', 'watchlist'):
        return jsonify({'error': 'Invalid tag type'}), 400
    try:
        from src.db import get_session, init_db
        from src import repositories
        init_db()
        with get_session() as session:
            repositories.remove_tag(session, imdb_id=imdb_id, tag=tag)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'success': True})


@app.route('/api/tags', methods=['GET'])
def get_tags():
    try:
        from src.db import get_session, init_db
        from src import repositories
        init_db()
        with get_session() as session:
            def tag_to_dict(t):
                return {'imdb_id': t.imdb_id, 'title': t.title, 'poster_url': t.poster_url,
                        'tagged_at': t.tagged_at.isoformat() if t.tagged_at else None}
            return jsonify({
                'liked':     [tag_to_dict(t) for t in repositories.get_tags(session, 'liked')],
                'disliked':  [tag_to_dict(t) for t in repositories.get_tags(session, 'disliked')],
                'watchlist': [tag_to_dict(t) for t in repositories.get_tags(session, 'watchlist')],
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    try:
        from src.db import get_session, init_db
        from src import repositories
        init_db()
        with get_session() as session:
            return jsonify({
                'rating_weights': repositories.get_preference(
                    session, 'rating_weights',
                    default={'imdb': 0.3, 'rt_critics': 0.2, 'rt_audience': 0.15, 'metacritic': 0.15, 'streaming': 0.2}
                ),
                'visible_ratings': repositories.get_preference(
                    session, 'visible_ratings',
                    default=['imdb', 'rt_critics', 'rt_audience', 'metacritic']
                ),
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preferences', methods=['PUT'])
def update_preferences():
    data = request.json or {}
    try:
        from src.db import get_session, init_db
        from src import repositories
        init_db()
        with get_session() as session:
            if 'rating_weights' in data:
                repositories.set_preference(session, 'rating_weights', data['rating_weights'])
            if 'visible_ratings' in data:
                repositories.set_preference(session, 'visible_ratings', data['visible_ratings'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'success': True})


@app.route('/api/recommendations', methods=['GET'])
def api_recommendations():
    try:
        from src.db import get_session, init_db
        from src import repositories
        from src.recommendation_engine import get_or_rebuild_recommendations
        init_db()
        with get_session() as session:
            liked_count = len(repositories.get_liked_imdb_ids(session))
            if liked_count < 3:
                return jsonify({
                    'shows': [],
                    'message': f'Like at least 3 titles to get recommendations. You have {liked_count} so far.',
                })
            recs = get_or_rebuild_recommendations(session)
            result = []
            for rec in recs[:20]:
                cache = repositories.get_show_cache(session, rec.imdb_id)
                if cache:
                    result.append({
                        'imdb_id': rec.imdb_id,
                        'title': rec.title or cache.title,
                        'poster_url': rec.poster_url or cache.poster_url,
                        'similarity_score': rec.similarity_score,
                        'release_year': cache.release_year,
                        'genres': cache.genres_list(),
                    })
            return jsonify({'shows': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def main():
    print("\n" + "=" * 50)
    print("  StreamFind — Web UI")
    print("=" * 50)
    print("\n  Starting server at http://localhost:5000")
    print("  Press Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
