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
        "rating": "Rating",
        "year": "Release Year",
        "title": "Title",
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
        return {
            "country": self.country,
            "show_type": self.show_type,
            "genres": self.genres,
            "rating_min": self.rating_min,
            "order_by": self.order_by,
            "order_direction": self.order_direction,
            "output_language": self.output_language,
            "series_granularity": self.series_granularity,
        }
    
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
class AppConfig:
    """Main application configuration."""
    api: APIConfig = field(default_factory=APIConfig.from_env)
    search: SearchParams = field(default_factory=SearchParams.from_env)
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load full config from environment."""
        return cls(
            api=APIConfig.from_env(),
            search=SearchParams.from_env(),
        )


def create_env_template(filepath: str = ".env.template") -> None:
    """Create a template .env file with all available options."""
    template = """# Streaming Availability API Configuration
# Copy this file to .env and fill in your values

# === API Configuration ===
RAPID_API_KEY=your_api_key_here
API_BASE_URL=https://streaming-availability.p.rapidapi.com/shows/search/filters
API_HOST=streaming-availability.p.rapidapi.com

# === Search Parameters ===
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

# Order by: rating, year, title
SEARCH_ORDER_BY=rating

# Order direction: desc, asc
SEARCH_ORDER_DIRECTION=desc

# Output language
SEARCH_OUTPUT_LANGUAGE=en

# Series granularity: show, episode
SEARCH_SERIES_GRANULARITY=show
"""
    with open(filepath, "w") as f:
        f.write(template)
    print(f"Created template file: {filepath}")


if __name__ == "__main__":
    # Create template when run directly
    create_env_template()
