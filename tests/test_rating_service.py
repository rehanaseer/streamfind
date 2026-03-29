"""Tests for rating normalization and weighted average computation."""

import pytest
from src.rating_service import normalize_ratings, compute_weighted_rating, apply_weighted_rating, sort_shows


class TestNormalizeRatings:
    def test_imdb_multiplied_by_10(self):
        result = normalize_ratings({'rating_imdb': 7.4})
        assert result['rating_imdb'] == 74.0

    def test_tmdb_multiplied_by_10(self):
        result = normalize_ratings({'rating_tmdb': 6.9})
        assert result['rating_tmdb'] == 69.0

    def test_rt_critics_unchanged(self):
        result = normalize_ratings({'rating_rt_critics': 85})
        assert result['rating_rt_critics'] == 85

    def test_rt_audience_unchanged(self):
        result = normalize_ratings({'rating_rt_audience': 72})
        assert result['rating_rt_audience'] == 72

    def test_metacritic_unchanged(self):
        result = normalize_ratings({'rating_metacritic': 68})
        assert result['rating_metacritic'] == 68

    def test_none_values_stay_none(self):
        result = normalize_ratings({'rating_imdb': None, 'rating_rt_critics': None})
        assert result['rating_imdb'] is None
        assert result['rating_rt_critics'] is None

    def test_missing_keys_not_added(self):
        result = normalize_ratings({'rating_imdb': 7.4})
        assert 'rating_rt_critics' not in result


class TestComputeWeightedRating:
    def test_single_source(self):
        result = compute_weighted_rating({'imdb': 80}, {'imdb': 1.0})
        assert result == 80.0

    def test_equal_weights(self):
        result = compute_weighted_rating(
            {'imdb': 80, 'rt_critics': 60},
            {'imdb': 1.0, 'rt_critics': 1.0}
        )
        assert result == 70.0

    def test_all_zero_weights_returns_zero(self):
        result = compute_weighted_rating(
            {'imdb': 80, 'rt_critics': 60},
            {'imdb': 0.0, 'rt_critics': 0.0}
        )
        assert result == 0.0

    def test_none_rating_skipped(self):
        result = compute_weighted_rating(
            {'imdb': 80, 'rt_critics': None},
            {'imdb': 0.5, 'rt_critics': 0.5}
        )
        assert result == 80.0

    def test_unequal_weights(self):
        result = compute_weighted_rating(
            {'imdb': 100, 'rt_critics': 0},
            {'imdb': 0.9, 'rt_critics': 0.1}
        )
        assert result == 90.0

    def test_uses_normalized_field_names(self):
        # compute_weighted_rating also accepts 'rating_imdb' style keys
        result = compute_weighted_rating(
            {'rating_imdb': 80},
            {'imdb': 1.0}
        )
        assert result == 80.0

    def test_empty_inputs_returns_zero(self):
        result = compute_weighted_rating({}, {})
        assert result == 0.0


class TestApplyWeightedRating:
    def test_adds_weighted_rating_field(self):
        show = {'rating_imdb': 7.4, 'rating': 75}
        weights = {'imdb': 1.0}
        result = apply_weighted_rating(show, weights)
        assert 'weighted_rating' in result
        assert result['weighted_rating'] == 74.0

    def test_modifies_in_place(self):
        show = {'rating_imdb': 8.0}
        weights = {'imdb': 1.0}
        apply_weighted_rating(show, weights)
        assert show['weighted_rating'] == 80.0


class TestSortShows:
    def _shows(self):
        return [
            {'title': 'Alpha', 'weighted_rating': 85, 'rating_imdb': 8.5, 'release_year': 2020},
            {'title': 'Beta',  'weighted_rating': 70, 'rating_imdb': 7.0, 'release_year': 2022},
            {'title': 'Gamma', 'weighted_rating': 90, 'rating_imdb': 9.0, 'release_year': 2018},
        ]

    def test_sort_by_weighted_rating_desc(self):
        result = sort_shows(self._shows(), 'weighted_rating', 'desc')
        assert result[0]['title'] == 'Gamma'
        assert result[-1]['title'] == 'Beta'

    def test_sort_by_year_asc(self):
        result = sort_shows(self._shows(), 'year', 'asc')
        assert result[0]['release_year'] == 2018

    def test_sort_by_title_asc(self):
        result = sort_shows(self._shows(), 'title', 'asc')
        assert result[0]['title'] == 'Alpha'
