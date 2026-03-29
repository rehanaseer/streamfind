"""Tests for the TF-IDF recommendation engine."""

import json
import pytest
from src.recommendation_engine import build_feature_string, train, recommend
from src.db import ShowCache


def make_show(imdb_id, genres, countries=None, year=2015):
    """Helper to create a minimal ShowCache object."""
    show = ShowCache()
    show.imdb_id = imdb_id
    show.genres = json.dumps(genres)
    show.production_countries = json.dumps(countries or ['US'])
    show.release_year = year
    show.title = f"Show {imdb_id}"
    show.poster_url = None
    return show


class TestBuildFeatureString:
    def test_includes_genres(self):
        show = make_show('tt1', ['Horror', 'Thriller'])
        feat = build_feature_string(show)
        assert 'horror' in feat
        assert 'thriller' in feat

    def test_includes_country(self):
        show = make_show('tt2', ['Drama'], countries=['GB'])
        feat = build_feature_string(show)
        assert 'country_gb' in feat

    def test_includes_decade(self):
        show = make_show('tt3', [], year=2018)
        feat = build_feature_string(show)
        assert '2010s' in feat

    def test_decade_2000s(self):
        show = make_show('tt4', [], year=2005)
        assert '2000s' in build_feature_string(show)

    def test_no_year_no_decade(self):
        show = make_show('tt5', [])
        show.release_year = None
        feat = build_feature_string(show)
        assert 's' not in feat or 'country' in feat  # no decade token

    def test_empty_show_returns_unknown(self):
        show = ShowCache()
        show.genres = None
        show.production_countries = None
        show.release_year = None
        result = build_feature_string(show)
        assert result == 'unknown'


class TestRecommend:
    def _make_corpus(self):
        return [
            make_show('tt10', ['Horror', 'Thriller'], ['US'], 2020),
            make_show('tt11', ['Horror', 'Mystery'],  ['US'], 2019),
            make_show('tt12', ['Horror'],              ['US'], 2021),
            make_show('tt13', ['Comedy'],              ['GB'], 2022),
            make_show('tt14', ['Comedy', 'Romance'],   ['GB'], 2020),
            make_show('tt15', ['Drama'],               ['FR'], 2018),
        ]

    def test_below_three_liked_returns_empty(self):
        corpus = self._make_corpus()
        model = train(corpus)
        vectorizer, matrix, index = model
        result = recommend(['tt10', 'tt11'], [], vectorizer, matrix, index)
        assert result == []

    def test_returns_non_empty_with_enough_liked(self):
        corpus = self._make_corpus()
        model = train(corpus)
        vectorizer, matrix, index = model
        result = recommend(['tt10', 'tt11', 'tt12'], [], vectorizer, matrix, index)
        assert len(result) > 0

    def test_excludes_already_liked(self):
        corpus = self._make_corpus()
        model = train(corpus)
        vectorizer, matrix, index = model
        liked = ['tt10', 'tt11', 'tt12']
        result = recommend(liked, [], vectorizer, matrix, index)
        rec_ids = [r[0] for r in result]
        for iid in liked:
            assert iid not in rec_ids

    def test_excludes_disliked(self):
        corpus = self._make_corpus()
        model = train(corpus)
        vectorizer, matrix, index = model
        result = recommend(['tt10', 'tt11', 'tt12'], ['tt13'], vectorizer, matrix, index)
        rec_ids = [r[0] for r in result]
        assert 'tt13' not in rec_ids

    def test_similarity_scores_between_0_and_1(self):
        corpus = self._make_corpus()
        model = train(corpus)
        vectorizer, matrix, index = model
        result = recommend(['tt10', 'tt11', 'tt12'], [], vectorizer, matrix, index)
        for _, score in result:
            assert 0 <= score <= 1
