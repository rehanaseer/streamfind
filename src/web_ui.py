"""
Web UI for Streaming Availability API.

A Flask-based web interface for searching streaming content.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template_string, request, jsonify, session
from src.config import APIConfig, SearchParams, AppConfig
from src.api_client import StreamingAPIClient

app = Flask(__name__)
app.secret_key = os.urandom(24)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Streaming Availability Search</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a25;
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.3);
            --text-primary: #f0f0f5;
            --text-secondary: #8888a0;
            --success: #10b981;
            --warning: #f59e0b;
            --border: #2a2a3a;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Sora', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            background-image: 
                radial-gradient(ellipse at 20% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 100%, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            text-align: center;
            padding: 3rem 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 2rem;
        }
        
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent), #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 2rem;
        }
        
        @media (max-width: 900px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .sidebar {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 1.5rem;
            border: 1px solid var(--border);
            height: fit-content;
            position: sticky;
            top: 2rem;
        }
        
        .form-section {
            margin-bottom: 1.5rem;
        }
        
        .form-section h3 {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-secondary);
            margin-bottom: 0.75rem;
            font-family: 'Space Mono', monospace;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        label {
            display: block;
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.375rem;
        }
        
        select, input[type="text"], input[type="number"], input[type="password"] {
            width: 100%;
            padding: 0.75rem 1rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-family: inherit;
            font-size: 0.9rem;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }
        
        select {
            cursor: pointer;
        }
        
        .btn {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, var(--accent), #8b5cf6);
            border: none;
            border-radius: 8px;
            color: white;
            font-family: inherit;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px var(--accent-glow);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .results-area {
            background: var(--bg-card);
            border-radius: 16px;
            border: 1px solid var(--border);
            min-height: 500px;
        }
        
        .results-header {
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .results-count {
            font-family: 'Space Mono', monospace;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .results-grid {
            padding: 1.5rem;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.25rem;
        }
        
        .show-card {
            background: var(--bg-secondary);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border);
            transition: transform 0.2s, border-color 0.2s;
        }
        
        .show-card:hover {
            transform: translateY(-4px);
            border-color: var(--accent);
        }
        
        .show-poster {
            width: 100%;
            height: 160px;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: var(--text-secondary);
        }
        
        .show-poster img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .show-info {
            padding: 1rem;
        }
        
        .show-title {
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.25rem;
            line-height: 1.3;
        }
        
        .show-year {
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-family: 'Space Mono', monospace;
        }
        
        .show-rating {
            display: inline-flex;
            align-items: center;
            gap: 0.375rem;
            background: rgba(16, 185, 129, 0.15);
            color: var(--success);
            padding: 0.25rem 0.625rem;
            border-radius: 100px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }
        
        .show-rating.low {
            background: rgba(245, 158, 11, 0.15);
            color: var(--warning);
        }
        
        .show-genres {
            margin-top: 0.625rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        
        .show-services {
            margin-top: 0.75rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.375rem;
        }
        
        .service-tag {
            background: var(--accent-glow);
            color: var(--accent);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 4rem 2rem;
            text-align: center;
        }
        
        .empty-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.3;
        }
        
        .empty-text {
            color: var(--text-secondary);
            max-width: 300px;
        }
        
        .loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 4rem;
        }
        
        .spinner {
            width: 48px;
            height: 48px;
            border: 3px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error-msg {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #ef4444;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 1.5rem;
        }
        
        .api-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
        }
        
        .status-dot.error {
            background: #ef4444;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎬 Streaming Search</h1>
            <p class="subtitle">Find movies and shows across streaming platforms</p>
        </header>
        
        <div class="main-grid">
            <aside class="sidebar">
                <form id="searchForm">
                    <div class="form-section">
                        <h3>API Configuration</h3>
                        <div class="form-group">
                            <label for="apiKey">RapidAPI Key</label>
                            <input type="password" id="apiKey" name="api_key" 
                                   placeholder="Enter your API key"
                                   value="{{ config.api.api_key }}">
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3>Search Filters</h3>
                        
                        <div class="form-group">
                            <label for="country">Country</label>
                            <select id="country" name="country">
                                {% for code, name in countries.items() %}
                                <option value="{{ code }}" {{ 'selected' if config.search.country == code }}>{{ name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="showType">Content Type</label>
                            <select id="showType" name="show_type">
                                {% for code, name in show_types.items() %}
                                <option value="{{ code }}" {{ 'selected' if config.search.show_type == code }}>{{ name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="genre">Genre</label>
                            <select id="genre" name="genres">
                                {% for code, name in genres.items() %}
                                <option value="{{ code }}" {{ 'selected' if config.search.genres == code }}>{{ name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="ratingMin">Minimum Rating (0-100)</label>
                            <input type="number" id="ratingMin" name="rating_min" 
                                   min="0" max="100" value="{{ config.search.rating_min }}">
                        </div>
                        
                        <div class="form-group">
                            <label for="orderBy">Sort By</label>
                            <select id="orderBy" name="order_by">
                                {% for code, name in order_options.items() %}
                                <option value="{{ code }}" {{ 'selected' if config.search.order_by == code }}>{{ name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="orderDir">Sort Direction</label>
                            <select id="orderDir" name="order_direction">
                                {% for code, name in direction_options.items() %}
                                <option value="{{ code }}" {{ 'selected' if config.search.order_direction == code }}>{{ name }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn" id="searchBtn">
                        Search Content
                    </button>
                    
                    <div class="api-status" id="apiStatus">
                        <span class="status-dot"></span>
                        <span>Ready to search</span>
                    </div>
                </form>
            </aside>
            
            <main class="results-area">
                <div class="results-header">
                    <h2>Results</h2>
                    <span class="results-count" id="resultsCount">0 items</span>
                </div>
                
                <div id="resultsContainer">
                    <div class="empty-state">
                        <div class="empty-icon">🎬</div>
                        <p class="empty-text">Configure your search parameters and click Search to find streaming content</p>
                    </div>
                </div>
            </main>
        </div>
    </div>
    
    <script>
        const form = document.getElementById('searchForm');
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsCount = document.getElementById('resultsCount');
        const searchBtn = document.getElementById('searchBtn');
        const apiStatus = document.getElementById('apiStatus');
        
        function showLoading() {
            resultsContainer.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p style="margin-top: 1rem; color: var(--text-secondary);">Searching...</p>
                </div>
            `;
            searchBtn.disabled = true;
            searchBtn.textContent = 'Searching...';
        }
        
        function showError(message) {
            resultsContainer.innerHTML = `<div class="error-msg">${message}</div>`;
        }
        
        function showEmpty() {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">😕</div>
                    <p class="empty-text">No results found. Try adjusting your search filters.</p>
                </div>
            `;
        }
        
        function renderResults(shows) {
            if (!shows || shows.length === 0) {
                showEmpty();
                resultsCount.textContent = '0 items';
                return;
            }
            
            resultsCount.textContent = `${shows.length} items`;
            
            const html = shows.map(show => `
                <div class="show-card">
                    <div class="show-poster">
                        ${show.poster_url 
                            ? `<img src="${show.poster_url}" alt="${show.title}" loading="lazy">`
                            : '🎬'
                        }
                    </div>
                    <div class="show-info">
                        <h3 class="show-title">${show.title}</h3>
                        <span class="show-year">${show.release_year || 'N/A'}</span>
                        ${show.rating ? `
                            <div class="show-rating ${show.rating < 70 ? 'low' : ''}">
                                ★ ${show.rating}/100
                            </div>
                        ` : ''}
                        ${show.genres && show.genres.length ? `
                            <div class="show-genres">${show.genres.slice(0, 3).join(' • ')}</div>
                        ` : ''}
                        <div class="show-services">
                            ${show.streaming_services.map(s => 
                                `<span class="service-tag">${s}</span>`
                            ).join('')}
                        </div>
                    </div>
                </div>
            `).join('');
            
            resultsContainer.innerHTML = `<div class="results-grid">${html}</div>`;
        }
        
        function updateStatus(success, message) {
            const dot = apiStatus.querySelector('.status-dot');
            const text = apiStatus.querySelector('span:last-child');
            dot.className = 'status-dot' + (success ? '' : ' error');
            text.textContent = message;
        }
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            showLoading();
            
            const formData = new FormData(form);
            const params = Object.fromEntries(formData.entries());
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params)
                });
                
                const data = await response.json();
                
                if (data.error) {
                    showError(data.error);
                    updateStatus(false, 'Search failed');
                } else {
                    renderResults(data.shows);
                    updateStatus(true, `Found ${data.total} results`);
                }
            } catch (err) {
                showError('Network error. Please try again.');
                updateStatus(false, 'Connection error');
            } finally {
                searchBtn.disabled = false;
                searchBtn.textContent = 'Search Content';
            }
        });
    </script>
</body>
</html>
"""


def get_config() -> AppConfig:
    """Get or create app configuration."""
    return AppConfig.from_env()


@app.route('/')
def index():
    """Render the main search page."""
    config = get_config()
    defaults = SearchParams()
    
    return render_template_string(
        HTML_TEMPLATE,
        config=config,
        countries=defaults.COUNTRIES,
        show_types=defaults.SHOW_TYPES,
        genres=defaults.GENRES,
        order_options=defaults.ORDER_BY_OPTIONS,
        direction_options=defaults.ORDER_DIRECTION_OPTIONS,
    )


@app.route('/api/search', methods=['POST'])
def search():
    """Handle search API requests."""
    data = request.json
    
    # Get API key from request or environment
    api_key = data.get('api_key', os.getenv('RAPID_API_KEY', ''))
    
    if not api_key:
        return jsonify({'error': 'API key is required. Please enter your RapidAPI key.'})
    
    # Create config and client
    api_config = APIConfig(api_key=api_key)
    client = StreamingAPIClient(api_config)
    
    # Create search params from request
    search_params = SearchParams(
        country=data.get('country', 'ca'),
        show_type=data.get('show_type', 'movie'),
        genres=data.get('genres', 'horror'),
        rating_min=str(data.get('rating_min', 70)),
        order_by=data.get('order_by', 'rating'),
        order_direction=data.get('order_direction', 'desc'),
    )
    
    # Fetch results
    result = client.fetch_all(search_params)
    
    if result.error:
        return jsonify({'error': result.error})
    
    # Convert shows to dictionaries
    shows = [show.to_dict() for show in result.shows]
    
    return jsonify({
        'shows': shows,
        'total': result.total_fetched,
        'pages': result.pages_fetched,
        'has_more': result.has_more,
    })


@app.route('/api/test', methods=['POST'])
def test_connection():
    """Test API connection."""
    data = request.json
    api_key = data.get('api_key', '')
    
    if not api_key:
        return jsonify({'success': False, 'message': 'API key required'})
    
    api_config = APIConfig(api_key=api_key)
    client = StreamingAPIClient(api_config)
    
    success, message = client.test_connection()
    return jsonify({'success': success, 'message': message})


def main():
    """Run the web server."""
    print("\n" + "=" * 50)
    print("  Streaming Availability Search - Web UI")
    print("=" * 50)
    print("\n  Starting server at http://localhost:5000")
    print("  Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()
