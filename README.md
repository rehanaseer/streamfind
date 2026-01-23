# Streaming Availability Search

A modular Python application for searching movies and TV shows across streaming platforms using the RapidAPI Streaming Availability API.

## Features

- **Modular Architecture**: Clean separation of concerns with config, API client, and UI modules
- **Dual Interface**: Both web UI and command-line interface
- **Flexible Configuration**: Support for environment variables and `.env` files
- **Pagination Support**: Handles API pagination automatically with both eager and lazy loading
- **Type-Safe**: Uses dataclasses for structured data handling
- **Dockerized**: Ready-to-run Docker setup with docker-compose

## Project Structure

```
streaming-app/
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose configuration
├── Makefile             # Convenient make commands
├── .env.example         # Environment variable template
├── .dockerignore        # Docker build exclusions
└── src/
    ├── __init__.py      # Package exports
    ├── config.py        # Configuration management
    ├── api_client.py    # API client and data models
    ├── cli.py           # Command-line interface
    └── web_ui.py        # Flask web interface
```

---

## Quick Start with Docker (Recommended)

### 1. Set up environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your RapidAPI key
nano .env  # or use any editor
```

### 2. Run with Docker Compose

```bash
# Start web UI
docker-compose up

# Or run in background
docker-compose up -d
```

Open http://localhost:5000 in your browser.

### 3. Other Docker Commands

```bash
# Run CLI mode
docker-compose --profile cli run --rm cli

# Development mode (hot reload)
docker-compose --profile dev up dev

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild after changes
docker-compose up --build
```

### Using Make (Optional)

If you have `make` installed:

```bash
make build    # Build Docker image
make up       # Start web UI
make cli      # Run CLI mode
make dev      # Development mode
make down     # Stop services
make clean    # Remove containers/images
make help     # Show all commands
```

---

## Local Installation (Without Docker)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up your API key

```bash
# Option 1: Environment variable
export RAPID_API_KEY=your_api_key_here

# Option 2: .env file
cp .env.example .env
# Edit .env with your API key
```

### 3. Run the application

```bash
# Web UI (default)
python main.py

# CLI mode
python main.py --cli
```

### Command-Line Options

```bash
python main.py --help          # Show help
python main.py --port 8080     # Custom port for web UI
python main.py --cli           # Run CLI instead of web UI
python main.py --create-env    # Create .env template
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RAPID_API_KEY` | Your RapidAPI key | (required) |
| `SEARCH_COUNTRY` | Country code (ca, us, gb, etc.) | ca |
| `SEARCH_SERVICE` | Streaming service | netflix |
| `SEARCH_SHOW_TYPE` | movie or series | movie |
| `SEARCH_GENRES` | Genre filter | horror |
| `SEARCH_RATING_MIN` | Minimum rating (0-100) | 70 |
| `SEARCH_ORDER_BY` | Sort field | rating |
| `SEARCH_ORDER_DIRECTION` | asc or desc | desc |
| `MAX_PAGES` | Max pages to fetch | 10 |

### Supported Values

**Countries**: ca, us, gb, au, de, fr, es, it, jp, br, mx, in

**Services**: netflix, prime, disney, hbo, apple, hulu, peacock, paramount, crave, stan

**Genres**: action, adventure, animation, comedy, crime, documentary, drama, family, fantasy, history, horror, music, mystery, romance, scifi, thriller, war, western

## Module Usage

You can also use the modules programmatically:

```python
from src import APIConfig, SearchParams, StreamingAPIClient

# Create configuration
api_config = APIConfig(api_key="your_key_here")
search_params = SearchParams(
    country="us",
    service="netflix",
    genres="comedy",
    rating_min="80"
)

# Create client and search
client = StreamingAPIClient(api_config)
result = client.fetch_all(search_params, max_pages=3)

# Process results
for show in result.shows:
    print(f"{show.title} ({show.release_year}) - Rating: {show.rating}")
    print(f"  Available on: {', '.join(show.get_service_names())}")
```

### Lazy Loading (Memory Efficient)

```python
# For large datasets, use lazy loading
for page_shows in client.fetch_lazy(search_params, max_pages=10):
    for show in page_shows:
        process_show(show)
```

## API Reference

### Classes

#### `APIConfig`
- `api_key`: RapidAPI key
- `base_url`: API endpoint URL
- `host`: API host header
- `from_env()`: Load from environment
- `get_headers()`: Get request headers
- `is_valid()`: Check if configuration is valid

#### `SearchParams`
- All search parameters as attributes
- `from_env()`: Load from environment
- `to_dict()`: Convert to API params
- `update(**kwargs)`: Create updated copy

#### `StreamingAPIClient`
- `fetch_all(params, max_pages)`: Fetch all results
- `fetch_lazy(params, max_pages)`: Generator for lazy loading
- `fetch_single_page(params, cursor)`: Fetch one page
- `test_connection()`: Test API connectivity

#### `Show`
- `title`, `release_year`, `rating`, etc.
- `streaming_services`: List of service info
- `get_service_names()`: Get unique service names
- `to_dict()`: Serialize to dictionary


