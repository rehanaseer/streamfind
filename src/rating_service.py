"""
Rating computation service for StreamFind.

Pure functions — no DB access, no API calls.
"""


def normalize_ratings(raw: dict) -> dict:
    """
    Normalize all rating sources to a 0-100 scale.

    IMDB and TMDB are stored on a 0-10 scale — multiply by 10.
    RT critics, RT audience, Metacritic are already 0-100.
    Missing (None) values stay None.
    """
    result = dict(raw)

    for field in ("rating_imdb", "rating_tmdb"):
        val = result.get(field)
        if val is not None:
            result[field] = round(float(val) * 10, 1)

    return result


def compute_weighted_rating(normalized: dict, weights: dict) -> float:
    """
    Compute a weighted average score from normalized ratings (all 0-100).

    Args:
        normalized: dict of {source_key: score} where all scores are 0-100.
                    None values are skipped.
        weights: dict of {source_key: weight} — weights need not sum to 1.

    Returns:
        Weighted average as float 0-100, or 0.0 if no valid sources.

    Formula:
        weighted = Σ(weight_i × score_i) / Σ(weight_i)
        where only sources with non-None scores and non-zero weights are counted.
    """
    # Map normalized dict keys to weight dict keys
    key_map = {
        "rating_imdb": "imdb",
        "rating_rt_critics": "rt_critics",
        "rating_rt_audience": "rt_audience",
        "rating_metacritic": "metacritic",
        "rating_tmdb": "tmdb",
        "rating_streaming": "streaming",
        # Also support direct keys
        "imdb": "imdb",
        "rt_critics": "rt_critics",
        "rt_audience": "rt_audience",
        "metacritic": "metacritic",
        "tmdb": "tmdb",
        "streaming": "streaming",
    }

    total_weight = 0.0
    weighted_sum = 0.0

    for norm_key, score in normalized.items():
        weight_key = key_map.get(norm_key)
        if weight_key is None:
            continue
        weight = weights.get(weight_key, 0.0)
        if weight <= 0 or score is None:
            continue
        weighted_sum += weight * float(score)
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(weighted_sum / total_weight, 1)


def apply_weighted_rating(show_dict: dict, weights: dict) -> dict:
    """
    Add 'weighted_rating' field to a show dict in-place.

    Normalizes raw ratings and computes the weighted average.
    Returns the same dict with 'weighted_rating' added.
    """
    raw = {
        "rating_imdb": show_dict.get("rating_imdb"),
        "rating_rt_critics": show_dict.get("rating_rt_critics"),
        "rating_rt_audience": show_dict.get("rating_rt_audience"),
        "rating_metacritic": show_dict.get("rating_metacritic"),
        "rating_tmdb": show_dict.get("rating_tmdb"),
        "rating_streaming": show_dict.get("rating"),
    }
    normalized = normalize_ratings(raw)
    show_dict["weighted_rating"] = compute_weighted_rating(normalized, weights)
    return show_dict


def sort_shows(shows: list, sort_by: str, direction: str = "desc") -> list:
    """
    Sort a list of show dicts by the given field.

    sort_by options: weighted_rating, imdb, rt_critics, rt_audience,
                     metacritic, tmdb_popularity, year, title
    """
    reverse = direction == "desc"

    key_map = {
        "weighted_rating": lambda s: s.get("weighted_rating") or 0,
        "imdb": lambda s: s.get("rating_imdb") or 0,
        "rt_critics": lambda s: s.get("rating_rt_critics") or 0,
        "rt_audience": lambda s: s.get("rating_rt_audience") or 0,
        "metacritic": lambda s: s.get("rating_metacritic") or 0,
        "tmdb_popularity": lambda s: s.get("popularity_tmdb") or 0,
        "year": lambda s: s.get("release_year") or 0,
        "title": lambda s: (s.get("title") or "").lower(),
        "rating": lambda s: s.get("rating") or 0,
    }

    key_fn = key_map.get(sort_by, key_map["weighted_rating"])
    return sorted(shows, key=key_fn, reverse=reverse)
