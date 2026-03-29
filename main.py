#!/usr/bin/env python3
"""
Streaming Availability Search - Main Entry Point

Usage:
    python main.py          # Run web UI (default)
    python main.py --cli    # Run command-line interface
    python main.py --help   # Show help
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Streaming Availability Search - Find movies and shows across streaming platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py              # Start web UI at http://localhost:5000
    python main.py --cli        # Start interactive CLI
    python main.py --port 8080  # Start web UI on custom port
    
Environment Variables:
    RAPID_API_KEY           Your RapidAPI key (required)
    SEARCH_COUNTRY          Default country code (e.g., 'ca', 'us')
    SEARCH_SERVICE          Default streaming service (e.g., 'netflix')
    SEARCH_SHOW_TYPE        Default show type ('movie' or 'series')
    SEARCH_GENRES           Default genre (e.g., 'horror', 'comedy')
    SEARCH_RATING_MIN       Minimum rating (0-100)
    MAX_PAGES               Maximum pages to fetch (default: 10)
        """
    )
    
    parser.add_argument(
        '--cli', 
        action='store_true',
        help='Run command-line interface instead of web UI'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port for web UI (default: 5000)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host for web UI (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--create-env',
        action='store_true',
        help='Create a template .env file and exit'
    )

    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize the database (create tables, seed defaults) and exit'
    )

    args = parser.parse_args()

    if args.create_env:
        from src.config import create_env_template
        create_env_template()
        print("\nEdit .env.template with your settings, then rename to .env")
        return

    if args.init_db:
        from src.db import init_db
        init_db()
        db_path = __import__('os').getenv('DB_PATH', 'data/streamfind.db')
        print(f"\nDatabase initialized at: {db_path}")
        print("Tables created: shows_cache, user_tags, user_preferences, recommendation_cache")
        return
    
    if args.cli:
        from src.cli import main as cli_main
        cli_main()
    else:
        from src.web_ui import app
        print("\n" + "=" * 50)
        print("  🎬 Streaming Availability Search")
        print("=" * 50)
        print(f"\n  Web UI: http://localhost:{args.port}")
        print("  Press Ctrl+C to stop\n")
        app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
