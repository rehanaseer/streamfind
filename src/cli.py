"""
Command-line interface for Streaming Availability API.

Provides an interactive terminal UI for searching streaming content.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import APIConfig, SearchParams, AppConfig
from src.api_client import StreamingAPIClient, Show


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(text: str):
    """Print a styled header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 60}{Colors.RESET}\n")


def print_subheader(text: str):
    """Print a styled subheader."""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}▸ {text}{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 40}{Colors.RESET}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def print_show(show: Show, index: int):
    """Print a single show with formatting."""
    rating_color = Colors.GREEN if (show.rating or 0) >= 70 else Colors.YELLOW
    
    print(f"\n{Colors.BOLD}{index}. {show.title}{Colors.RESET}", end="")
    if show.release_year:
        print(f" {Colors.DIM}({show.release_year}){Colors.RESET}")
    else:
        print()
    
    if show.rating:
        print(f"   {rating_color}★ Rating: {show.rating}/100{Colors.RESET}")
    
    if show.genres:
        print(f"   {Colors.DIM}Genres: {', '.join(show.genres[:3])}{Colors.RESET}")
    
    services = show.get_service_names()
    if services:
        print(f"   {Colors.CYAN}📺 Available on: {', '.join(services)}{Colors.RESET}")
    
    if show.imdb_id:
        print(f"   {Colors.DIM}IMDb: {show.imdb_id}{Colors.RESET}")


def select_option(options: dict, prompt: str, current: str = None) -> str:
    """
    Display options and let user select one.
    
    Args:
        options: Dictionary of {value: display_name}
        prompt: Prompt text
        current: Current selected value
    
    Returns:
        Selected value
    """
    print(f"\n{Colors.BOLD}{prompt}{Colors.RESET}")
    
    items = list(options.items())
    for i, (value, name) in enumerate(items, 1):
        marker = f"{Colors.GREEN}●{Colors.RESET}" if value == current else " "
        print(f"  {marker} {i}. {name} ({value})")
    
    while True:
        try:
            choice = input(f"\n{Colors.CYAN}Enter number (1-{len(items)}) or press Enter to keep current: {Colors.RESET}")
            if not choice and current:
                return current
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return items[idx][0]
            print_error("Invalid selection")
        except ValueError:
            print_error("Please enter a number")


def input_number(prompt: str, current: int, min_val: int = 0, max_val: int = 100) -> int:
    """Get a number input from user."""
    while True:
        try:
            value = input(f"{Colors.CYAN}{prompt} (current: {current}, {min_val}-{max_val}): {Colors.RESET}")
            if not value:
                return current
            num = int(value)
            if min_val <= num <= max_val:
                return num
            print_error(f"Please enter a number between {min_val} and {max_val}")
        except ValueError:
            print_error("Please enter a valid number")


def configure_search(params: SearchParams) -> SearchParams:
    """Interactive configuration of search parameters."""
    print_header("Configure Search Parameters")
    
    # Create instances to access the option dictionaries
    defaults = SearchParams()
    
    while True:
        print("\nCurrent Settings:")
        print(f"  1. Country: {defaults.COUNTRIES.get(params.country, params.country)}")
        print(f"  2. Type: {defaults.SHOW_TYPES.get(params.show_type, params.show_type)}")
        print(f"  3. Genre: {defaults.GENRES.get(params.genres, params.genres)}")
        print(f"  4. Min Rating: {params.rating_min}")
        print(f"  5. Order By: {defaults.ORDER_BY_OPTIONS.get(params.order_by, params.order_by)}")
        print(f"  6. Direction: {defaults.ORDER_DIRECTION_OPTIONS.get(params.order_direction, params.order_direction)}")
        print(f"  7. {Colors.GREEN}Done - Start Search{Colors.RESET}")
        print(f"  0. {Colors.RED}Cancel{Colors.RESET}")
        
        choice = input(f"\n{Colors.CYAN}Select option to change (0-7): {Colors.RESET}")
        
        if choice == "1":
            params = params.update(country=select_option(defaults.COUNTRIES, "Select Country:", params.country))
        elif choice == "2":
            params = params.update(show_type=select_option(defaults.SHOW_TYPES, "Select Show Type:", params.show_type))
        elif choice == "3":
            params = params.update(genres=select_option(defaults.GENRES, "Select Genre:", params.genres))
        elif choice == "4":
            params = params.update(rating_min=str(input_number("Enter minimum rating", int(params.rating_min))))
        elif choice == "5":
            params = params.update(order_by=select_option(defaults.ORDER_BY_OPTIONS, "Select Order By:", params.order_by))
        elif choice == "6":
            params = params.update(order_direction=select_option(defaults.ORDER_DIRECTION_OPTIONS, "Select Direction:", params.order_direction))
        elif choice == "7":
            return params
        elif choice == "0":
            return None
    
    return params


def run_search(client: StreamingAPIClient, params: SearchParams):
    """Run the search and display results."""
    print_header("Search Results")
    
    def progress_callback(page: int, count: int, total: int):
        print(f"\r{Colors.DIM}Fetching page {page}... ({total} shows found){Colors.RESET}", end="", flush=True)
    
    result = client.fetch_all(params, on_progress=progress_callback)
    print()  # New line after progress
    
    if result.error:
        print_error(f"Error during fetch: {result.error}")
    
    if not result.shows:
        print_info("No shows found matching your criteria.")
        return
    
    print_success(f"Found {result.total_fetched} shows across {result.pages_fetched} pages")
    
    if result.has_more:
        print_info("More results available (increase max pages to see more)")
    
    print_subheader("Results")
    
    # Display shows with pagination
    page_size = 10
    current_page = 0
    total_pages = (len(result.shows) + page_size - 1) // page_size
    
    while True:
        start = current_page * page_size
        end = min(start + page_size, len(result.shows))
        
        for i, show in enumerate(result.shows[start:end], start + 1):
            print_show(show, i)
        
        print(f"\n{Colors.DIM}Page {current_page + 1}/{total_pages}{Colors.RESET}")
        print(f"\n{Colors.CYAN}[N]ext page | [P]revious | [Q]uit to menu{Colors.RESET}")
        
        choice = input("> ").lower()
        
        if choice == 'n' and current_page < total_pages - 1:
            current_page += 1
            clear_screen()
            print_subheader(f"Results (Page {current_page + 1})")
        elif choice == 'p' and current_page > 0:
            current_page -= 1
            clear_screen()
            print_subheader(f"Results (Page {current_page + 1})")
        elif choice == 'q':
            break


def main_menu(config: AppConfig):
    """Display and handle main menu."""
    client = StreamingAPIClient(config.api)
    
    while True:
        print_header("Streaming Availability Search")
        
        print("  1. Search with current settings")
        print("  2. Configure search parameters")
        print("  3. Test API connection")
        print("  4. View current configuration")
        print("  5. Set API key")
        print("  0. Exit")
        
        choice = input(f"\n{Colors.CYAN}Select option: {Colors.RESET}")
        
        if choice == "1":
            if not config.api.is_valid():
                print_error("API key not configured. Please set your API key first (option 5).")
                input("Press Enter to continue...")
                continue
            run_search(client, config.search)
            input("\nPress Enter to continue...")
            
        elif choice == "2":
            new_params = configure_search(config.search)
            if new_params:
                config.search = new_params
                print_success("Configuration updated!")
            input("Press Enter to continue...")
            
        elif choice == "3":
            print_info("Testing connection...")
            success, message = client.test_connection()
            if success:
                print_success(message)
            else:
                print_error(message)
            input("Press Enter to continue...")
            
        elif choice == "4":
            print_subheader("Current Configuration")
            print(f"  API Key: {'*' * 8 + config.api.api_key[-4:] if config.api.api_key else 'Not set'}")
            print(f"  Base URL: {config.api.base_url}")
            print(f"\n  Search Parameters:")
            for key, value in config.search.to_dict().items():
                print(f"    {key}: {value}")
            input("\nPress Enter to continue...")
            
        elif choice == "5":
            api_key = input(f"{Colors.CYAN}Enter your RapidAPI key: {Colors.RESET}")
            if api_key:
                config.api.api_key = api_key
                client = StreamingAPIClient(config.api)  # Recreate client with new key
                print_success("API key updated!")
            input("Press Enter to continue...")
            
        elif choice == "0":
            print_info("Goodbye!")
            break
        
        clear_screen()


def main():
    """Main entry point for CLI."""
    clear_screen()
    
    # Load configuration
    config = AppConfig.from_env()
    
    # Check for API key in environment
    if not config.api.is_valid():
        print_header("Welcome to Streaming Search")
        print_info("API key not found in environment variables.")
        print_info("You can set it via the RAPID_API_KEY environment variable")
        print_info("or enter it manually in the application.\n")
    
    main_menu(config)


if __name__ == "__main__":
    main()
