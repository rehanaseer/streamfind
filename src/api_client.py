"""
API Client module for Streaming Availability API.

Handles all HTTP requests and pagination logic.
"""

import requests
from typing import Generator, Optional
from dataclasses import dataclass

from .config import APIConfig, SearchParams


@dataclass
class Show:
    """Represents a show/movie from the API."""
    title: str
    release_year: Optional[int]
    imdb_id: Optional[str]
    tmdb_id: Optional[str]
    show_type: str
    rating: Optional[int]
    overview: Optional[str]
    genres: list[str]
    streaming_services: list[dict]
    poster_url: Optional[str]
    raw_data: dict
    
    @classmethod
    def from_api_response(cls, data: dict, country: str = "ca") -> "Show":
        """Create a Show instance from API response data."""
        # Extract streaming services for the specified country
        streaming_options = data.get("streamingOptions", {})
        services = []
        
        if country in streaming_options:
            for option in streaming_options[country]:
                service_info = option.get("service", {})
                services.append({
                    "name": service_info.get("name", "Unknown"),
                    "id": service_info.get("id", ""),
                    "link": option.get("link", ""),
                    "type": option.get("type", ""),
                    "quality": option.get("quality", ""),
                })
        
        # Extract genres
        genres = [g.get("name", "") for g in data.get("genres", [])]
        
        return cls(
            title=data.get("title", "Unknown"),
            release_year=data.get("releaseYear"),
            imdb_id=data.get("imdbId"),
            tmdb_id=data.get("tmdbId"),
            show_type=data.get("showType", "unknown"),
            rating=data.get("rating"),
            overview=data.get("overview"),
            genres=genres,
            streaming_services=services,
            poster_url=data.get("imageSet", {}).get("verticalPoster", {}).get("w240"),
            raw_data=data,
        )
    
    def get_service_names(self) -> list[str]:
        """Get list of unique streaming service names."""
        return list(set(s["name"] for s in self.streaming_services))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "release_year": self.release_year,
            "imdb_id": self.imdb_id,
            "tmdb_id": self.tmdb_id,
            "show_type": self.show_type,
            "rating": self.rating,
            "overview": self.overview,
            "genres": self.genres,
            "streaming_services": self.get_service_names(),
            "poster_url": self.poster_url,
        }


@dataclass
class FetchResult:
    """Result of a fetch operation."""
    shows: list[Show]
    total_fetched: int
    pages_fetched: int
    has_more: bool
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        return self.error is None


class StreamingAPIClient:
    """Client for the Streaming Availability API."""
    
    def __init__(self, config: APIConfig):
        """Initialize the API client."""
        self.config = config
        self._session = requests.Session()
        self._session.headers.update(config.get_headers())
    
    def _make_request(self, params: dict) -> dict:
        """Make a single API request."""
        response = self._session.get(self.config.base_url, params=params)
        response.raise_for_status()
        return response.json()
    
    def fetch_all(
        self, 
        search_params: SearchParams, 
        max_pages: Optional[int] = None,
        on_progress: Optional[callable] = None,
    ) -> FetchResult:
        """
        Fetch all results from the API with pagination.
        
        Args:
            search_params: Search parameters
            max_pages: Maximum number of pages to fetch (None for all)
            on_progress: Optional callback(page_num, shows_count, total_count)
        
        Returns:
            FetchResult with all shows
        """
        all_shows = []
        cursor = None
        page_count = 0
        has_more = False
        
        params = search_params.to_dict()
        
        while True:
            if cursor:
                params["cursor"] = cursor
            
            try:
                data = self._make_request(params)
                
                shows_data = data.get("shows", [])
                shows = [
                    Show.from_api_response(s, search_params.country) 
                    for s in shows_data
                ]
                all_shows.extend(shows)
                
                page_count += 1
                
                if on_progress:
                    on_progress(page_count, len(shows), len(all_shows))
                
                has_more = data.get("hasMore", False)
                if not has_more:
                    break
                
                if max_pages and page_count >= max_pages:
                    break
                
                cursor = data.get("nextCursor")
                if not cursor:
                    break
                    
            except requests.exceptions.RequestException as e:
                return FetchResult(
                    shows=all_shows,
                    total_fetched=len(all_shows),
                    pages_fetched=page_count,
                    has_more=has_more,
                    error=str(e),
                )
        
        return FetchResult(
            shows=all_shows,
            total_fetched=len(all_shows),
            pages_fetched=page_count,
            has_more=has_more,
        )
    
    def fetch_lazy(
        self, 
        search_params: SearchParams,
        max_pages: Optional[int] = None,
    ) -> Generator[list[Show], None, None]:
        """
        Generator function to fetch pages lazily.
        
        Args:
            search_params: Search parameters
            max_pages: Maximum number of pages to fetch (None for all)
        
        Yields:
            List of Show objects for each page
        """
        cursor = None
        page_count = 0
        
        params = search_params.to_dict()
        
        while True:
            if cursor:
                params["cursor"] = cursor
            
            try:
                data = self._make_request(params)
                
                shows_data = data.get("shows", [])
                shows = [
                    Show.from_api_response(s, search_params.country) 
                    for s in shows_data
                ]
                
                page_count += 1
                
                yield shows
                
                has_more = data.get("hasMore", False)
                if not has_more:
                    break
                
                if max_pages and page_count >= max_pages:
                    break
                
                cursor = data.get("nextCursor")
                if not cursor:
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"Error fetching page {page_count + 1}: {e}")
                break
    
    def fetch_single_page(
        self, 
        search_params: SearchParams,
        cursor: Optional[str] = None,
    ) -> tuple[list[Show], Optional[str], bool]:
        """
        Fetch a single page of results.
        
        Args:
            search_params: Search parameters
            cursor: Pagination cursor (None for first page)
        
        Returns:
            Tuple of (shows, next_cursor, has_more)
        """
        params = search_params.to_dict()
        if cursor:
            params["cursor"] = cursor
        
        data = self._make_request(params)
        
        shows_data = data.get("shows", [])
        shows = [
            Show.from_api_response(s, search_params.country) 
            for s in shows_data
        ]
        
        next_cursor = data.get("nextCursor")
        has_more = data.get("hasMore", False)
        
        return shows, next_cursor, has_more
    
    def search_by_title(
        self,
        title: str,
        country: str = "ca",
        show_type: str = "",
        series_granularity: str = "show",
        output_language: str = "en",
    ) -> list[Show]:
        """Search for shows by title using the title search endpoint."""
        title_url = self.config.base_url.replace(
            "/shows/search/filters", "/shows/search/title"
        )
        params: dict = {
            "title": title,
            "country": country,
            "series_granularity": series_granularity,
            "output_language": output_language,
        }
        if show_type:
            params["show_type"] = show_type

        response = self._session.get(title_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Title endpoint returns a list directly
        shows_data = data if isinstance(data, list) else data.get("shows", [])
        return [Show.from_api_response(s, country) for s in shows_data]

    def test_connection(self) -> tuple[bool, str]:
        """
        Test the API connection.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.config.is_valid():
            return False, "Invalid configuration: API key is missing"
        
        try:
            params = SearchParams().to_dict()
            response = self._session.get(
                self.config.base_url, 
                params=params,
                timeout=10,
            )
            
            if response.status_code == 200:
                return True, "Connection successful"
            elif response.status_code == 401:
                return False, "Invalid API key"
            elif response.status_code == 403:
                return False, "Access forbidden - check your subscription"
            elif response.status_code == 429:
                return False, "Rate limit exceeded"
            else:
                return False, f"Unexpected status code: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error - check your internet"
        except Exception as e:
            return False, f"Error: {str(e)}"
