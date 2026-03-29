"""
Configuration module for Streaming Availability API.

Supports loading configuration from:
1. Environment variables (highest priority)
2. .env file
3. Default values (lowest priority)
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class APIConfig:
    """API connection configuration."""
    api_key: str = ""
    base_url: str = "https://streaming-availability.p.rapidapi.com/shows/search/filters"
    host: str = "streaming-availability.p.rapidapi.com"
    
    @classmethod
    def from_env(cls) -> "APIConfig":
        """Load API config from environment variables."""
        return cls(
            api_key=os.getenv("RAPID_API_KEY", ""),
            base_url=os.getenv("API_BASE_URL", cls.base_url),
            host=os.getenv("API_HOST", cls.host),
        )
    
    def get_headers(self) -> dict:
        """Get headers for API requests."""
        return {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.host,
        }
    
    def is_valid(self) -> bool:
        """Check if API config is valid."""
        return bool(self.api_key and self.base_url and self.host)


@dataclass
class SearchParams:
    """Search parameters for the streaming availability API."""
    country: str = "ca"
    show_type: str = "movie"
    genres: str = "horror"
    rating_min: str = "70"
    order_by: str = "rating"
    order_direction: str = "desc"
    output_language: str = "en"
    series_granularity: str = "show"
    services: str = ""
    
    # Available options for each parameter
    COUNTRIES: dict = field(default_factory=lambda: {
        "ca": "Canada",
        "us": "United States",
        "gb": "United Kingdom",
        "au": "Australia",
        "de": "Germany",
        "fr": "France",
        "es": "Spain",
        "it": "Italy",
        "jp": "Japan",
        "br": "Brazil",
        "mx": "Mexico",
        "in": "India",
    })
    
    STREAMING_SERVICES: dict = field(default_factory=lambda: {
        "netflix": "Netflix",
        "prime": "Prime Video",
        "disney": "Disney+",
        "hulu": "Hulu",
        "hbo": "HBO Max",
        "apple": "Apple TV+",
        "paramount": "Paramount+",
        "peacock": "Peacock",
        "mubi": "MUBI",
        "curiosity": "Curiosity Stream",
    })

    SHOW_TYPES: dict = field(default_factory=lambda: {
        "movie": "Movies",
        "series": "TV Series",
    })
    
    GENRES: dict = field(default_factory=lambda: {
        "action": "Action",
        "adventure": "Adventure",
        "animation": "Animation",
        "comedy": "Comedy",
        "crime": "Crime",
        "documentary": "Documentary",
        "drama": "Drama",
        "family": "Family",
        "fantasy": "Fantasy",
        "history": "History",
        "horror": "Horror",
        "music": "Music",
        "mystery": "Mystery",
        "romance": "Romance",
        "scifi": "Science Fiction",
        "thriller": "Thriller",
        "war": "War",
        "western": "Western",
    })
    
    ORDER_BY_OPTIONS: dict = field(default_factory=lambda: {
        "weighted_rating": "Weighted Score",
        "imdb": "IMDB",
        "rt_critics": "RT Critics",
        "rt_audience": "RT Audience",
        "metacritic": "Metacritic",
        "tmdb_popularity": "Popularity",
        "rating": "Streaming Rating",
        "year": "Release Year",
        "title": "Title",
    })

    PRODUCTION_COUNTRIES: dict = field(default_factory=lambda: {
        "US": "United States",
        "GB": "United Kingdom",
        "FR": "France",
        "DE": "Germany",
        "IT": "Italy",
        "ES": "Spain",
        "JP": "Japan",
        "KR": "South Korea",
        "IN": "India",
        "CN": "China",
        "AU": "Australia",
        "CA": "Canada",
        "MX": "Mexico",
        "BR": "Brazil",
        "SE": "Sweden",
        "DK": "Denmark",
        "NO": "Norway",
    })
    
    ORDER_DIRECTION_OPTIONS: dict = field(default_factory=lambda: {
        "desc": "Descending",
        "asc": "Ascending",
    })
    
    @classmethod
    def from_env(cls) -> "SearchParams":
        """Load search params from environment variables."""
        return cls(
            country=os.getenv("SEARCH_COUNTRY", cls.country),
            show_type=os.getenv("SEARCH_SHOW_TYPE", cls.show_type),
            genres=os.getenv("SEARCH_GENRES", cls.genres),
            rating_min=os.getenv("SEARCH_RATING_MIN", cls.rating_min),
            order_by=os.getenv("SEARCH_ORDER_BY", cls.order_by),
            order_direction=os.getenv("SEARCH_ORDER_DIRECTION", cls.order_direction),
            output_language=os.getenv("SEARCH_OUTPUT_LANGUAGE", cls.output_language),
            series_granularity=os.getenv("SEARCH_SERIES_GRANULARITY", cls.series_granularity),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API request."""
        params = {
            "country": self.country,
            "rating_min": int(self.rating_min) if self.rating_min else 0,
            "order_by": self.order_by,
            "order_direction": self.order_direction,
            "output_language": self.output_language,
            "series_granularity": self.series_granularity,
        }
        if self.show_type:
            params["show_type"] = self.show_type
        if self.genres:
            params["genres"] = self.genres
        if self.services:
            params["services"] = self.services
        return params
    
    def update(self, **kwargs) -> "SearchParams":
        """Return a new SearchParams with updated values."""
        current = self.to_dict()
        current.update(kwargs)
        # Remove the class-level option dictionaries from kwargs
        for key in ["COUNTRIES", "SHOW_TYPES", "GENRES", 
                    "ORDER_BY_OPTIONS", "ORDER_DIRECTION_OPTIONS"]:
            current.pop(key, None)
        return SearchParams(**current)


@dataclass
class RatingConfig:
    """Configuration for rating enrichment (MDBList primary, OMDB/TMDB fallback)."""
    mdblist_api_key: str = ""
    omdb_api_key: str = ""
    tmdb_api_key: str = ""
    db_path: str = "data/streamfind.db"
    cache_ttl_days: int = 7
    default_weights: dict = field(default_factory=lambda: {
        "streaming": 0.1,
        "imdb": 0.25,
        "rt_critics": 0.2,
        "rt_audience": 0.2,
        "metacritic": 0.15,
        "tmdb": 0.1,
    })

    @classmethod
    def from_env(cls) -> "RatingConfig":
        return cls(
            mdblist_api_key=os.getenv("MDBLIST_API_KEY", ""),
            omdb_api_key=os.getenv("OMDB_API_KEY", ""),
            tmdb_api_key=os.getenv("TMDB_API_KEY", ""),
            db_path=os.getenv("DB_PATH", "data/streamfind.db"),
            cache_ttl_days=int(os.getenv("RATING_CACHE_TTL_DAYS", "7")),
        )


@dataclass
class AppConfig:
    """Main application configuration."""
    api: APIConfig = field(default_factory=APIConfig.from_env)
    search: SearchParams = field(default_factory=SearchParams.from_env)
    rating: RatingConfig = field(default_factory=RatingConfig.from_env)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load full config from environment."""
        return cls(
            api=APIConfig.from_env(),
            search=SearchParams.from_env(),
            rating=RatingConfig.from_env(),
        )


def create_env_template(filepath: str = ".env.template") -> None:
    """Create a template .env file with all available options."""
    template = """# StreamFind Configuration
# Copy this file to .env and fill in your values

# === Streaming Availability API (RapidAPI) ===
RAPID_API_KEY=your_rapidapi_key_here
API_BASE_URL=https://streaming-availability.p.rapidapi.com/shows/search/filters
API_HOST=streaming-availability.p.rapidapi.com

# === Rating Enrichment APIs ===
# OMDB (free 1000/day): https://www.omdbapi.com/apikey.aspx
OMDB_API_KEY=your_omdb_key_here

# TMDB (free): https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_tmdb_key_here

# === Database ===
DB_PATH=data/streamfind.db
RATING_CACHE_TTL_DAYS=7

# === Search Defaults ===
# Country codes: ca, us, gb, au, de, fr, es, it, jp, br, mx, in
SEARCH_COUNTRY=ca

# Show types: movie, series
SEARCH_SHOW_TYPE=movie

# Genres: action, adventure, animation, comedy, crime, documentary, drama,
#         family, fantasy, history, horror, music, mystery, romance, scifi,
#         thriller, war, western
SEARCH_GENRES=horror

# Minimum rating (0-100)
SEARCH_RATING_MIN=70

# Order by: weighted_rating, imdb, rt_critics, rt_audience, metacritic,
#           tmdb_popularity, rating, year, title
SEARCH_ORDER_BY=weighted_rating

# Order direction: desc, asc
SEARCH_ORDER_DIRECTION=desc

# Output language
SEARCH_OUTPUT_LANGUAGE=en

# Series granularity: show, episode
SEARCH_SERIES_GRANULARITY=show

# === Web Server ===
WEB_PORT=8080
FLASK_ENV=production
"""
    with open(filepath, "w") as f:
        f.write(template)
    print(f"Created template file: {filepath}")


if __name__ == "__main__":
    # Create template when run directly
    create_env_template()
