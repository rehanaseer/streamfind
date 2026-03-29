#!/usr/bin/env python3
"""Generates a detailed technical report PDF for StreamFind."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import KeepTogether
import datetime

OUTPUT = "StreamFind_Technical_Report.pdf"

# ── Colour palette ──────────────────────────────────────────────────────────
ACCENT      = colors.HexColor("#FA320A")   # brand orange-red
DARK        = colors.HexColor("#1a1a2e")   # near-black
MID         = colors.HexColor("#2d2d44")   # dark navy
LIGHT_GRAY  = colors.HexColor("#f5f5f5")
MID_GRAY    = colors.HexColor("#e0e0e0")
CODE_BG     = colors.HexColor("#f0f0f0")
WHITE       = colors.white
TEXT        = colors.HexColor("#333333")

# ── Styles ───────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def style(name, **kw):
    s = ParagraphStyle(name, **kw)
    return s

TITLE = style("ReportTitle",
    fontSize=28, leading=34, textColor=WHITE,
    fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6)

SUBTITLE = style("ReportSubtitle",
    fontSize=13, leading=18, textColor=colors.HexColor("#cccccc"),
    fontName="Helvetica", alignment=TA_CENTER, spaceAfter=4)

H1 = style("H1",
    fontSize=18, leading=22, textColor=ACCENT,
    fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=8)

H2 = style("H2",
    fontSize=14, leading=18, textColor=DARK,
    fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6)

H3 = style("H3",
    fontSize=12, leading=15, textColor=MID,
    fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)

BODY = style("Body",
    fontSize=10, leading=14, textColor=TEXT,
    fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=6)

BODY_SMALL = style("BodySmall",
    fontSize=9, leading=13, textColor=TEXT,
    fontName="Helvetica", spaceAfter=4)

CODE = style("Code",
    fontSize=8.5, leading=12, textColor=colors.HexColor("#222222"),
    fontName="Courier", backColor=CODE_BG, spaceAfter=6,
    leftIndent=10, rightIndent=10, borderPadding=(4, 4, 4, 4))

BULLET = style("Bullet",
    fontSize=10, leading=14, textColor=TEXT,
    fontName="Helvetica", leftIndent=16, spaceAfter=3)

CAPTION = style("Caption",
    fontSize=8, leading=11, textColor=colors.gray,
    fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=8)

# ── Table helpers ─────────────────────────────────────────────────────────────
def header_row_style(cols):
    return [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("GRID",       (0, 0), (-1, -1), 0.4, MID_GRAY),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]

def make_table(data, col_widths, style_extra=None):
    ts = TableStyle(header_row_style(len(data[0])) + (style_extra or []))
    return Table(data, colWidths=col_widths, style=ts, repeatRows=1)

def p(text, sty=None): return Paragraph(text, sty or BODY)
def h1(text): return Paragraph(text, H1)
def h2(text): return Paragraph(text, H2)
def h3(text): return Paragraph(text, H3)
def sp(h=0.3): return Spacer(1, h*cm)
def hr(): return HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceAfter=8)
def code(text): return Paragraph(text.replace("\n","<br/>").replace(" ", "&nbsp;"), CODE)

def bullets(items, sty=None):
    s = sty or BULLET
    return [Paragraph(f"• &nbsp;{i}", s) for i in items]

def cell(text, bold=False, color=None, size=9):
    fn = "Helvetica-Bold" if bold else "Helvetica"
    col = f'<font color="{color}">' if color else ""
    end = "</font>" if color else ""
    return Paragraph(f"{col}{text}{end}", ParagraphStyle("cell",
        fontSize=size, leading=13, fontName=fn, textColor=TEXT))

# ── Cover page ────────────────────────────────────────────────────────────────
def cover(story):
    # Dark banner
    story.append(Table(
        [[Paragraph("StreamFind", TITLE)],
         [Paragraph("Technical Architecture & Design Report", SUBTITLE)],
         [Paragraph(f"Generated {datetime.date.today().strftime('%B %d, %Y')}", SUBTITLE)]],
        colWidths=[17*cm],
        style=TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), DARK),
            ("TOPPADDING",    (0,0), (-1,-1), 20),
            ("BOTTOMPADDING", (0,0), (-1,-1), 20),
            ("LEFTPADDING",   (0,0), (-1,-1), 20),
            ("RIGHTPADDING",  (0,0), (-1,-1), 20),
        ])
    ))
    story.append(sp(0.6))
    story.append(Table(
        [[cell("A full-stack Python web application for discovering movies and TV shows\n"
               "across streaming platforms — enriched with multi-source ratings,\n"
               "weighted scoring, and ML-based personalised recommendations.", size=11)]],
        colWidths=[17*cm],
        style=TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#fff8f6")),
            ("LINEBEFORE",    (0,0), (0,-1), 4, ACCENT),
            ("TOPPADDING",    (0,0), (-1,-1), 14),
            ("BOTTOMPADDING", (0,0), (-1,-1), 14),
            ("LEFTPADDING",   (0,0), (-1,-1), 16),
            ("RIGHTPADDING",  (0,0), (-1,-1), 16),
            ("BOX",           (0,0), (-1,-1), 0.5, ACCENT),
        ])
    ))
    story.append(sp(0.5))

    # Key stats row
    stats = [
        ("4", "External APIs"),
        ("4", "DB Tables"),
        ("13", "Python Modules"),
        ("3", "JS Modules"),
        ("50+", "Test Cases"),
    ]
    row = [[Table([[cell(v, bold=True, size=22)],[cell(l, size=8)]],
                  colWidths=[3*cm],
                  style=TableStyle([
                      ("ALIGN",(0,0),(-1,-1),"CENTER"),
                      ("TOPPADDING",(0,0),(-1,-1),10),
                      ("BOTTOMPADDING",(0,0),(-1,-1),10),
                  ])) for v,l in stats]]
    story.append(Table(row, colWidths=[3.4*cm]*5,
        style=TableStyle([
            ("BACKGROUND",(0,0),(-1,-1), LIGHT_GRAY),
            ("BOX",(0,0),(-1,-1),0.5,MID_GRAY),
            ("INNERGRID",(0,0),(-1,-1),0.3,MID_GRAY),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ])))
    story.append(PageBreak())

# ── TOC ───────────────────────────────────────────────────────────────────────
def toc(story):
    story.append(h1("Table of Contents"))
    sections = [
        ("1.", "Project Overview & Goals"),
        ("2.", "High-Level Architecture"),
        ("3.", "Technology Stack & Rationale"),
        ("4.", "Entry Point — main.py"),
        ("5.", "Configuration Layer — src/config.py"),
        ("6.", "API Client — src/api_client.py"),
        ("7.", "Database Layer — src/db.py & src/repositories.py"),
        ("8.", "Rating Enrichment — src/rating_client.py & src/rating_service.py"),
        ("9.", "ML Recommendations — src/recommendation_engine.py"),
        ("10.", "Web UI & Routes — src/web_ui.py"),
        ("11.", "Command-Line Interface — src/cli.py"),
        ("12.", "Frontend — Templates, CSS & JavaScript"),
        ("13.", "Docker & Deployment"),
        ("14.", "Testing Strategy"),
        ("15.", "Key Design Decisions & Trade-offs"),
        ("16.", "Data Flow Walkthroughs"),
        ("17.", "Security Considerations"),
        ("18.", "Future Roadmap"),
    ]
    data = [[cell(n, bold=True), cell(t)] for n, t in sections]
    story.append(Table(data, colWidths=[1.5*cm, 15.5*cm],
        style=TableStyle([
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, LIGHT_GRAY]),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("RIGHTPADDING",  (0,0), (-1,-1), 6),
            ("GRID",          (0,0), (-1,-1), 0.3, MID_GRAY),
        ])))
    story.append(PageBreak())

# ── Section 1: Overview ───────────────────────────────────────────────────────
def section_overview(story):
    story.append(h1("1. Project Overview & Goals"))
    story.append(p(
        "StreamFind is a single-user, self-hosted web application that solves a real consumer "
        "problem: with dozens of streaming services each holding thousands of titles, discovering "
        "content worth watching is increasingly difficult. StreamFind aggregates titles from "
        "multiple platforms via the RapidAPI Streaming Availability API, then enriches every "
        "result with ratings from four independent sources (IMDB, Rotten Tomatoes, Metacritic, "
        "TMDB) and surfaces a single <b>weighted score</b> the user can tune to their own taste. "
        "After the user rates enough content, a machine-learning engine produces personalised "
        "recommendations using TF-IDF cosine similarity."
    ))
    story.append(h2("Primary Goals"))
    story += bullets([
        "Aggregate streaming availability from a single API call.",
        "Enrich every title with multi-source critical and audience ratings.",
        "Expose a configurable, weighted scoring system via an interactive settings panel.",
        "Provide ML-driven personalised recommendations after a minimum of 3 liked titles.",
        "Persist user preferences, tags, and enriched data in a local SQLite database with TTL-based caching.",
        "Offer both a modern web UI and an interactive CLI from the same Python backend.",
        "Be runnable locally in under five minutes via Docker Compose.",
    ])
    story.append(h2("Scope Constraints (Deliberate)"))
    story += bullets([
        "Single-user — no authentication, no user accounts.",
        "SQLite only — no PostgreSQL or Redis; the architecture makes migration trivial (one FK addition).",
        "No real-time updates — cache TTL is 7 days; no WebSockets.",
        "Vanilla JavaScript — no React/Vue; keeps the frontend dependency-free.",
    ])
    story.append(PageBreak())

# ── Section 2: Architecture ───────────────────────────────────────────────────
def section_architecture(story):
    story.append(h1("2. High-Level Architecture"))
    story.append(p(
        "The application follows a layered architecture with strict separation of concerns. "
        "Each layer has a single clearly-defined responsibility and communicates only with "
        "the layer directly below it."
    ))

    layers = [
        ["Layer", "Modules", "Responsibility"],
        ["Presentation", "templates/, static/", "Jinja2 HTML + CSS/JS — renders UI, calls API endpoints"],
        ["Web / Route", "src/web_ui.py", "Flask routes, request parsing, response formatting"],
        ["Application", "src/rating_service.py\nsrc/recommendation_engine.py", "Business logic — scoring, ML, normalisation"],
        ["Integration", "src/api_client.py\nsrc/rating_client.py", "All outbound HTTP — streaming API, OMDB, TMDB, MDBList"],
        ["Data Access", "src/repositories.py", "ALL database queries — single source of truth"],
        ["Infrastructure", "src/db.py\nsrc/config.py", "ORM engine, session management, configuration"],
    ]
    rows = [[cell(r[0], bold=(i==0)), cell(r[1]), cell(r[2])] for i,r in enumerate(layers)]
    story.append(make_table(rows, [3*cm, 5*cm, 9*cm]))
    story.append(sp())

    story.append(h2("Data Flow Summary"))
    story.append(p(
        "A user search request travels: Browser → Flask route → StreamingAPIClient (RapidAPI) → "
        "batch_enrich() → OmdbClient / TmdbClient / MdblistClient → repositories (cache read/write) → "
        "rating_service (normalise + weight) → JSON response → search.js (card render)."
    ))

    story.append(h2("External API Integration Points"))
    apis = [
        ["API", "Purpose", "Rate Limit", "Fallback"],
        ["RapidAPI Streaming Availability", "Title list + streaming options", "Varies by plan", "None — required"],
        ["MDBList", "IMDB, RT critics/audience, Metacritic, TMDB (single call)", "1,000 req/day (free)", "Falls through to OMDB"],
        ["OMDB", "IMDB rating, RT critics, Metacritic", "1,000 req/day (free)", "Used if MDBList gaps"],
        ["TMDB", "TMDB score, popularity, production countries", "~40 req/10 s (free)", "Countries skipped if missing"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(apis)]
    story.append(make_table(rows, [4.5*cm, 5.5*cm, 3*cm, 4*cm]))
    story.append(PageBreak())

# ── Section 3: Tech stack ─────────────────────────────────────────────────────
def section_tech(story):
    story.append(h1("3. Technology Stack & Rationale"))

    stack = [
        ["Technology", "Version", "Why chosen"],
        ["Python", "3.12", "Modern match-statement, type hints, dataclasses — developer productivity"],
        ["Flask", "≥ 2.3", "Lightweight; no ORM coupling, no magic — fits a 450-line route file well"],
        ["SQLAlchemy", "≥ 2.0", "2.0 API is explicit; easy migration from SQLite → Postgres; ORM prevents SQL injection"],
        ["SQLite", "stdlib", "Zero-configuration, file-based, Docker-volume-mountable; multi-user path is a one-migration change"],
        ["scikit-learn", "≥ 1.3", "TF-IDF + cosine similarity in <10 lines; no custom ML framework overhead"],
        ["requests", "≥ 2.28", "Simple, well-documented HTTP; API calls are sequential, so async is unnecessary"],
        ["Jinja2", "Flask bundled", "Familiar Django-like templating; server-side render avoids JS hydration complexity"],
        ["Vanilla JS", "ES2020", "No build step; three small focused modules; no React/Vue overhead for a single-user app"],
        ["python-dotenv", "≥ 1.0", "12-factor config; keeps secrets out of code"],
        ["pytest", "≥ 7.4", "Fixtures, parametrize, clean syntax; pairs naturally with Flask test client"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(stack)]
    story.append(make_table(rows, [3.5*cm, 2.5*cm, 11*cm]))
    story.append(PageBreak())

# ── Section 4: main.py ────────────────────────────────────────────────────────
def section_main(story):
    story.append(h1("4. Entry Point — main.py"))
    story.append(p(
        "<b>main.py</b> (~99 lines) is the single entry point for all run modes. "
        "It uses Python's <b>argparse</b> to branch into four distinct modes:"
    ))
    modes = [
        ["Flag", "Behaviour"],
        ["(none)", "Starts Flask web server at http://localhost:5000"],
        ["--cli", "Launches interactive terminal interface (src/cli.py)"],
        ["--init-db", "Creates all SQLite tables and seeds default preferences"],
        ["--create-env", "Writes a .env.template file listing all configurable variables"],
        ["--port PORT", "Override default Flask port (5000)"],
        ["--host HOST", "Override default Flask bind address (127.0.0.1)"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(modes)]
    story.append(make_table(rows, [4*cm, 13*cm]))
    story.append(sp())
    story.append(p(
        "Environment variables (RAPID_API_KEY, country, show type, genres, min rating) are loaded "
        "via <b>python-dotenv</b> before any Flask code is imported. This ensures configuration is "
        "always available from the process environment, consistent with 12-factor app principles."
    ))
    story.append(PageBreak())

# ── Section 5: config.py ──────────────────────────────────────────────────────
def section_config(story):
    story.append(h1("5. Configuration Layer — src/config.py"))
    story.append(p(
        "All application configuration is expressed as <b>Python dataclasses</b>. "
        "Each class has a <code>from_env()</code> factory method that reads from "
        "<code>os.environ</code>, which is populated by <b>python-dotenv</b> on startup. "
        "This approach gives type safety, IDE autocomplete, and makes testing trivial — "
        "tests simply set environment variables before calling <code>from_env()</code>."
    ))

    story.append(h2("Key Dataclasses"))

    classes = [
        ["Class", "Fields", "Purpose"],
        ["APIConfig", "api_key, base_url, host", "RapidAPI credentials + endpoint; get_headers() builds the required X-RapidAPI-* headers"],
        ["SearchParams", "country, show_type, genres, rating_min, order_by, services + 4 reference dicts", "All search filter state; to_dict() converts to RapidAPI query params; update() returns a new instance (immutable updates)"],
        ["RatingConfig", "mdblist_key, omdb_key, tmdb_key, db_path, cache_ttl_days", "Rating enrichment credentials and cache policy"],
        ["AppConfig", "api: APIConfig, search: SearchParams, rating: RatingConfig", "Composite root config — passed through to route handlers"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(classes)]
    story.append(make_table(rows, [3*cm, 5.5*cm, 8.5*cm]))

    story.append(sp())
    story.append(h2("Reference Data in SearchParams"))
    story.append(p(
        "SearchParams embeds four dicts: COUNTRIES (12), STREAMING_SERVICES (10), "
        "SHOW_TYPES (2), GENRES (18), and ORDER_BY_OPTIONS (9). "
        "Keeping these inside the config class (rather than a separate constants module) "
        "means the frontend templates receive the full option set directly from config — "
        "no duplication between Python and HTML."
    ))
    story.append(PageBreak())

# ── Section 6: api_client.py ──────────────────────────────────────────────────
def section_api_client(story):
    story.append(h1("6. API Client — src/api_client.py"))
    story.append(p(
        "The <b>StreamingAPIClient</b> wraps the RapidAPI Streaming Availability v4 endpoint. "
        "It holds a persistent <code>requests.Session</code> to reuse TCP connections "
        "across paginated requests, reducing latency on multi-page fetches."
    ))

    story.append(h2("Show Dataclass"))
    story.append(p(
        "The <b>Show</b> class is a lightweight data container populated from the raw API JSON "
        "via <code>from_api_response(data, country)</code>. It flattens nested streaming objects "
        "into a flat list of <code>{service, link, quality}</code> dicts and exposes "
        "<code>to_dict()</code> for JSON serialisation. Keeping this class thin — no business "
        "logic — means the API client is purely responsible for HTTP and parsing."
    ))

    story.append(h2("Pagination Strategy"))
    story.append(p(
        "The RapidAPI uses cursor-based pagination (<code>cursor</code> / <code>nextCursor</code>). "
        "StreamingAPIClient exposes three strategies:"
    ))
    strats = [
        ["Method", "Use case", "Notes"],
        ["fetch_single_page(params, cursor)", "Web UI search (one page at a time)", "Returns (shows, next_cursor, has_more); caller manages pagination state"],
        ["fetch_all(params, max_pages, on_progress)", "Eager: fetch everything upfront", "Optional progress callback; used for large pre-filter pools"],
        ["fetch_lazy(params, max_pages)", "Generator: memory-efficient streaming", "Yields pages one at a time; for CLI and batch processing"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(strats)]
    story.append(make_table(rows, [5*cm, 5*cm, 7*cm]))

    story.append(sp())
    story.append(h2("Error Handling"))
    story.append(p(
        "<code>test_connection()</code> returns structured error messages distinguishing "
        "invalid key, forbidden, rate limit, timeout, and connection error — giving users "
        "actionable feedback rather than a generic HTTP error code."
    ))
    story.append(PageBreak())

# ── Section 7: DB layer ───────────────────────────────────────────────────────
def section_db(story):
    story.append(h1("7. Database Layer — src/db.py & src/repositories.py"))

    story.append(h2("ORM Models (src/db.py)"))
    story.append(p(
        "Four SQLAlchemy declarative models map to SQLite tables. "
        "The engine is lazily initialised (singleton via a module-level variable) "
        "and <code>get_session()</code> is a context manager that commits on clean exit "
        "and rolls back on any exception — preventing partial writes."
    ))

    tables = [
        ["Table / Model", "Key Columns", "Design Rationale"],
        ["shows_cache\n(ShowCache)", "imdb_id (PK), title, release_year, genres (JSON), production_countries (JSON), rating_imdb/rt_critics/rt_audience/metacritic/tmdb, ratings_fetched_at", "Single cache row per show keyed by IMDB ID. JSON columns avoid a genres join table. ratings_fetched_at enables TTL without a separate expiry column."],
        ["user_tags\n(UserTag)", "id, imdb_id, tag, title, poster_url, tagged_at", "Unique constraint on (imdb_id, tag). Mutual exclusivity (liked↔disliked) enforced in repository layer, not DB constraint, for cleaner semantics."],
        ["user_preferences\n(UserPreference)", "key (unique), value (JSON text)", "Simple key-value store. JSON values allow storing dicts (weights) and lists (visible_ratings) without extra columns."],
        ["recommendation_cache\n(RecommendationCache)", "imdb_id, title, poster_url, similarity_score, based_on_tags (JSON), computed_at", "Pre-computed recs stored so page loads are instant. based_on_tags detects when liked set changes and triggers a rebuild."],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(tables)]
    story.append(make_table(rows, [4*cm, 5.5*cm, 7.5*cm]))

    story.append(sp())
    story.append(h2("Repository Pattern (src/repositories.py)"))
    story.append(p(
        "Every database query — create, read, update, delete — lives exclusively in "
        "<b>repositories.py</b>. Routes in web_ui.py call repository functions and receive "
        "plain Python objects or dicts. This strict boundary means:"
    ))
    story += bullets([
        "Tests can swap an in-memory SQLite session without touching route code.",
        "SQL queries are never scattered across multiple files.",
        "Changing the storage backend (e.g., PostgreSQL) requires changes only in repositories.py and db.py.",
        "The Claude Code CLAUDE.md explicitly lists this as a critical architectural rule.",
    ])

    story.append(h3("Key Repository Functions"))
    fns = [
        ["Function", "Behaviour"],
        ["upsert_show_cache(session, data)", "INSERT OR REPLACE with auto-serialisation of list fields to JSON"],
        ["get_stale_imdb_ids(session, ttl_days)", "Returns IDs with missing ratings or ratings_fetched_at older than TTL"],
        ["upsert_tag(session, imdb_id, tag, ...)", "Enforces mutual exclusivity: liking deletes any existing dislike row, and vice versa"],
        ["get_tags_for_shows(session, imdb_ids)", "Returns dict {imdb_id: [tags]} — used to annotate search results in a single query"],
        ["get_preference(session, key, default)", "JSON-decodes value; returns default if key absent"],
        ["write_recommendations_cache(session, recs, ids)", "Truncates and replaces the entire cache in one transaction"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(fns)]
    story.append(make_table(rows, [6.5*cm, 10.5*cm]))
    story.append(PageBreak())

# ── Section 8: Rating ─────────────────────────────────────────────────────────
def section_rating(story):
    story.append(h1("8. Rating Enrichment — src/rating_client.py & src/rating_service.py"))

    story.append(h2("Multi-API Enrichment Pipeline (rating_client.py)"))
    story.append(p(
        "The enrichment pipeline is designed around three guiding principles: "
        "<b>cache-first</b>, <b>fallback chains</b>, and <b>minimal API calls</b>."
    ))

    story.append(h3("API Clients"))
    clients = [
        ["Client", "Endpoint", "Data provided", "Strategy"],
        ["MdblistClient", "mdblist.com/api/", "IMDB, RT critics, RT audience, Metacritic, TMDB — all in one call", "Primary source. One HTTP call per show gives all five ratings."],
        ["OmdbClient", "omdbapi.com/", "IMDB, RT critics, Metacritic", "Fallback for any gaps left by MDBList."],
        ["TmdbClient", "api.themoviedb.org/3/", "TMDB vote_average, popularity, production_countries", "Always called — only TMDB provides production countries needed for filtering."],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(clients)]
    story.append(make_table(rows, [3*cm, 4*cm, 5*cm, 5*cm]))

    story.append(sp())
    story.append(h3("batch_enrich() Flow"))
    story += bullets([
        "Check cache freshness: ratings_fetched_at ≥ cutoff AND has any rating AND has production countries → skip API calls.",
        "If stale: call MDBList → fill any None fields from OMDB → always call TMDB for countries + popularity.",
        "Merge cache row with Show object → write back to DB via upsert_show_cache().",
        "Return list of enriched dicts ready for weighted scoring.",
    ])

    story.append(h2("Weighted Scoring (rating_service.py)"))
    story.append(p(
        "All rating computation is implemented as <b>pure functions</b> — no side effects, "
        "no database access. This makes them trivially testable and reusable from both "
        "the web route and the CLI."
    ))

    story.append(h3("Normalisation"))
    norms = [
        ["Source", "Raw scale", "Normalised to 0–100", "Why"],
        ["IMDB", "0.0–10.0", "× 10", "Bring to same scale as RT/Metacritic"],
        ["TMDB vote_average", "0.0–10.0", "× 10", "Same as IMDB"],
        ["RT Critics", "0–100", "No change", "Already percentage"],
        ["RT Audience", "0–100", "No change", "Already percentage"],
        ["Metacritic", "0–100", "No change", "Already percentage"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(norms)]
    story.append(make_table(rows, [3.5*cm, 3*cm, 4*cm, 6.5*cm]))

    story.append(sp())
    story.append(h3("Weighted Formula"))
    story.append(p(
        "weighted = Σ(weight_i × score_i) / Σ(weight_i for non-None scores)"
    ))
    story.append(p(
        "Dividing by the sum of <i>active</i> weights (not total) prevents penalising shows "
        "where one source has no data — e.g., a documentary with no RT audience score "
        "is not unfairly lowered."
    ))
    story.append(PageBreak())

# ── Section 9: ML ─────────────────────────────────────────────────────────────
def section_ml(story):
    story.append(h1("9. ML Recommendations — src/recommendation_engine.py"))
    story.append(p(
        "The recommendation engine uses <b>TF-IDF (Term Frequency–Inverse Document Frequency) "
        "with cosine similarity</b> — a well-understood content-based filtering technique "
        "that requires no user-to-user data and works with zero cold-start problems beyond "
        "the minimum 3-like requirement."
    ))

    story.append(h2("Feature Engineering"))
    story.append(p(
        "<code>build_feature_string(show)</code> converts a ShowCache row into a text document "
        "for TF-IDF vectorisation. The feature string combines:"
    ))
    story += bullets([
        "<b>Genres</b>: lowercased, spaces removed (e.g., 'Science Fiction' → 'science_fiction')",
        "<b>Production countries</b>: prefixed 'country_' to avoid collisions with genre terms",
        "<b>Decade</b>: derived from release_year (e.g., 2018 → '2010s') — captures era without overfitting to exact year",
    ])
    story.append(p(
        "This compact representation captures the most discriminating content features "
        "without requiring plot text (which many shows lack) or cast data (which changes rapidly)."
    ))

    story.append(h2("Training & Recommendation"))
    steps = [
        ["Step", "Function", "Detail"],
        ["1. Vectorise", "train(all_shows)", "TfidfVectorizer with min_df=1 fits on all cached shows. Returns vectorizer, TF-IDF matrix, and imdb_id → row index."],
        ["2. Build profile", "recommend(liked_ids, ...)", "Averages TF-IDF vectors of all liked shows into a single 'taste profile' vector."],
        ["3. Subtract dislikes", "recommend()", "profile -= 0.5 × avg(disliked vectors). Moves the profile away from unwanted content at half-strength."],
        ["4. Score candidates", "recommend()", "Cosine similarity between profile and every row in the TF-IDF matrix."],
        ["5. Filter & rank", "recommend()", "Excludes already-tagged shows. Returns top-N by score (only scores > 0)."],
        ["6. Cache results", "get_or_rebuild_recommendations()", "Writes top-20 with similarity scores to recommendation_cache table."],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(steps)]
    story.append(make_table(rows, [1.5*cm, 4.5*cm, 11*cm]))

    story.append(sp())
    story.append(h2("Cache Invalidation"))
    story.append(p(
        "Recommendations are rebuilt when either: (a) the cache is older than 24 hours, "
        "or (b) the set of liked imdb_ids has changed since the cache was last computed "
        "(checked by comparing the stored <code>based_on_tags</code> JSON against current likes). "
        "This avoids stale recs after the user likes/dislikes a show."
    ))

    story.append(h2("Minimum Threshold"))
    story.append(p(
        "A minimum of <b>3 liked titles</b> is required before the model is trained. "
        "Below this threshold, there is insufficient signal to produce meaningful recommendations, "
        "and cosine similarity on a single averaged vector would be heavily biased toward "
        "whatever one title happened to look like."
    ))
    story.append(PageBreak())

# ── Section 10: Web UI ────────────────────────────────────────────────────────
def section_webui(story):
    story.append(h1("10. Web UI & Routes — src/web_ui.py"))
    story.append(p(
        "The Flask app (~450 lines) is divided into page routes and API routes. "
        "All mutating operations live under <code>/api/</code> and return JSON. "
        "Page routes return rendered Jinja2 templates."
    ))

    story.append(h2("Route Inventory"))
    routes = [
        ["Method", "Path", "Type", "Description"],
        ["GET",    "/",                        "Page",   "Search page — passes full config (countries, genres, services) to template"],
        ["GET",    "/watchlist",               "Page",   "Fetches watchlist tags, enriches with cache data, renders card grid"],
        ["GET",    "/recommendations",         "Page",   "Checks liked count; calls get_or_rebuild_recommendations(); renders top-20"],
        ["POST",   "/api/search",              "API",    "Core search. Title search OR filter search. Enriches, scores, attaches tags. Returns {shows, next_cursor, has_more}"],
        ["POST",   "/api/test",               "API",    "Tests RapidAPI key connectivity"],
        ["POST",   "/api/tag",                "API",    "Adds/updates a tag (liked, disliked, watchlist)"],
        ["DELETE", "/api/tag/<id>/<tag>",     "API",    "Removes a specific tag"],
        ["GET",    "/api/tags",               "API",    "Returns all tags grouped by type"],
        ["GET",    "/api/preferences",        "API",    "Returns rating_weights and visible_ratings"],
        ["PUT",    "/api/preferences",        "API",    "Saves rating_weights and/or visible_ratings"],
        ["GET",    "/api/recommendations",    "API",    "Returns recommendation list as JSON (for AJAX)"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(routes)]
    story.append(make_table(rows, [1.8*cm, 5.5*cm, 1.8*cm, 7.9*cm]))

    story.append(sp())
    story.append(h2("/api/search Contract (Critical)"))
    story.append(p(
        "The CLAUDE.md designates the /api/search response shape as a <b>critical contract</b> "
        "that must never be broken, since search.js depends on it:"
    ))
    story += bullets([
        "<b>shows</b>: Array of enriched show objects (always present, may be empty)",
        "<b>next_cursor</b>: String cursor for next page, or null if none",
        "<b>has_more</b>: Boolean — false for title searches, true if more filter pages exist",
    ])

    story.append(h2("Title Search vs Filter Search"))
    story.append(p(
        "If the request body contains a non-empty <code>title</code> field, the route calls "
        "<code>search_by_title()</code> and returns <code>has_more: false</code> and "
        "<code>next_cursor: null</code>. Otherwise it uses <code>fetch_single_page()</code> "
        "with cursor-based pagination. This distinction is critical — the production country "
        "filter requires fetching a larger pool (up to 18 pages) then filtering client-side, "
        "while title search is single-call."
    ))
    story.append(PageBreak())

# ── Section 11: CLI ───────────────────────────────────────────────────────────
def section_cli(story):
    story.append(h1("11. Command-Line Interface — src/cli.py"))
    story.append(p(
        "The CLI provides the same core functionality (search, filter, configure) as the "
        "web UI, useful for headless servers or users who prefer the terminal. "
        "It shares the same APIConfig, SearchParams, and StreamingAPIClient — "
        "demonstrating the clean separation of the backend from the presentation layer."
    ))
    story.append(h2("Key Components"))
    story += bullets([
        "<b>Colors class</b>: 9 ANSI escape code constants for colour-coded terminal output.",
        "<b>select_option()</b>: Renders a numbered menu and reads a validated integer input — the core interactive primitive.",
        "<b>configure_search()</b>: Walks through all SearchParams fields with select_option() calls.",
        "<b>run_search()</b>: Executes fetch with a progress callback that prints dots, then paginates results (10/page, N/P/Q keys).",
        "<b>main_menu()</b>: State machine loop: Search | Configure | Test Connection | View Config | Set API Key | Exit.",
    ])
    story.append(h2("Design Rationale"))
    story.append(p(
        "The CLI was included to support power users and CI/batch workflows. "
        "By reusing the same backend classes, there is no logic duplication. "
        "The stateless search result display (paginate with N/P) was chosen over "
        "a curses-based full-screen UI to avoid the complexity and cross-platform "
        "compatibility issues of curses."
    ))
    story.append(PageBreak())

# ── Section 12: Frontend ──────────────────────────────────────────────────────
def section_frontend(story):
    story.append(h1("12. Frontend — Templates, CSS & JavaScript"))

    story.append(h2("Template Architecture"))
    story.append(p(
        "Jinja2 templates follow a strict inheritance hierarchy. "
        "<b>base.html</b> defines the shell: fixed navigation bar, filter bar placeholder, "
        "CSS imports, and JS import blocks. Child templates (<code>index.html</code>, "
        "<code>watchlist.html</code>, <code>recommendations.html</code>) extend base.html "
        "and fill named blocks (<code>content</code>, <code>extra_js</code>)."
    ))

    templates = [
        ["Template", "Extends", "Key Content"],
        ["base.html", "—", "Nav bar (logo, Watchlist badge, For You link), CSS imports (main.css, tags.css), JS blocks"],
        ["index.html", "base.html", "3-row filter bar, collapsible settings panel, hero / results grid; loads search.js, ratings.js, tags.js"],
        ["watchlist.html", "base.html", "Watchlist card grid with remove buttons; inline JS for DELETE /api/tag"],
        ["recommendations.html", "base.html", "Similarity score badge, weighted rating badge, tag buttons on hover; empty state for <3 likes"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(templates)]
    story.append(make_table(rows, [4*cm, 3*cm, 10*cm]))

    story.append(sp())
    story.append(h2("CSS Design System (static/css/main.css — ~713 lines)"))
    story.append(p(
        "The stylesheet is structured around CSS custom properties (variables) for the colour "
        "palette, allowing global theme changes from one place. Key design decisions:"
    ))
    story += bullets([
        "<b>CSS Variables</b>: --bg, --card-bg, --text, --accent (#FA320A) drive the dark theme.",
        "<b>Fixed Nav + Filter Bar</b>: Nav at 60px, filter bar at 136px — both fixed-position so content scrolls beneath.",
        "<b>Card Grid</b>: repeat(auto-fill, minmax(155px, 1fr)) — responsive without media query breakpoints.",
        "<b>2:3 Aspect Ratio</b>: Cards use padding-bottom: 150% to enforce poster dimensions regardless of image availability.",
        "<b>Hover Overlay</b>: Dark gradient overlay with transform: translateY(-4px) and image scale(1.05) for depth.",
        "<b>Skeleton Loading</b>: Shimmer animation (background-position slide) on grey placeholder cards while fetching.",
        "<b>Rating Chips</b>: Colour-coded by source — IMDB yellow, RT red, Metacritic green, TMDB blue.",
        "<b>Tags CSS (tags.css)</b>: Circular 24×24px semi-transparent buttons, opacity:0 by default, revealed on card:hover.",
    ])

    story.append(h2("JavaScript Modules"))
    story.append(p(
        "Three vanilla ES2020 modules, loaded in dependency order: "
        "<b>ratings.js</b> → <b>tags.js</b> → <b>search.js</b>."
    ))

    modules = [
        ["Module", "State managed", "Key responsibility"],
        ["ratings.js\n(~222 lines)", "ratingWeights, visibleRatings, activeProfile", "Loads /api/preferences on page load. Manages weight sliders and visible-rating toggles. Exports buildRatingChips(show) → HTML. Four profile presets: Critics, Audience, Balanced, Custom."],
        ["tags.js\n(~80 lines)", "None (stateless)", "Exports buildTagButtons(imdbId, title, poster, activeTags) → HTML. handleTagClick() performs optimistic UI toggle then POST/DELETE to /api/tag; reverts on network error."],
        ["search.js\n(~242 lines)", "cursorHistory[], nextCursor, currentPage, lastParams, currentTags", "Form submit handler, pagination (prev/next), card HTML generation via buildCard(s). Session state persisted to sessionStorage so back-navigation restores results. Shows skeletons, error, empty states."],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(modules)]
    story.append(make_table(rows, [3.5*cm, 4*cm, 9.5*cm]))

    story.append(sp())
    story.append(h2("Optimistic UI Pattern (tags.js)"))
    story.append(p(
        "When a user clicks ♥ (like), the button class is toggled <i>immediately</i> — "
        "before the network request completes. If the POST fails, the class is reverted. "
        "This pattern makes the UI feel instantaneous on slow connections while remaining "
        "consistent on failure. The mutual-exclusivity rule (liked removes dislike) is "
        "mirrored in JavaScript so the DOM update appears correct without waiting for the server."
    ))
    story.append(PageBreak())

# ── Section 13: Docker ────────────────────────────────────────────────────────
def section_docker(story):
    story.append(h1("13. Docker & Deployment"))

    story.append(h2("Multi-Stage Dockerfile"))
    story.append(p(
        "The Dockerfile uses a two-stage build to minimise the final image size "
        "and follow security best practices."
    ))

    stages = [
        ["Stage", "Base image", "Purpose"],
        ["builder", "python:3.12-slim", "Installs gcc (build dependency), creates /opt/venv, installs all Python packages into the venv."],
        ["production", "python:3.12-slim", "Copies only /opt/venv from builder (no gcc, no build artefacts). Creates non-root appuser. Copies app code owned by appuser."],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(stages)]
    story.append(make_table(rows, [2.5*cm, 4*cm, 10.5*cm]))

    story.append(sp())
    story.append(h2("Security Design in Dockerfile"))
    story += bullets([
        "<b>Non-root user</b>: Container runs as <code>appuser</code>, not root — limits blast radius if the process is compromised.",
        "<b>Read-only source code</b>: Application code is copied with appuser ownership; no write access needed.",
        "<b>No secrets in image</b>: API keys injected at runtime via environment variables — never baked into the image layer.",
        "<b>Healthcheck</b>: Python requests check to localhost:5000 every 30 s with 10 s timeout and 5 s start delay.",
    ])

    story.append(h2("docker-compose.yml — Service Profiles"))
    profiles = [
        ["Service", "Profile", "Purpose", "Key Settings"],
        ["web", "(default)", "Production web server", "Port 8080→5000; named volume for SQLite; json-file log driver; health check"],
        ["cli", "cli", "Interactive terminal", "stdin_open: true, tty: true; command: --cli; no ports exposed"],
        ["dev", "dev", "Hot-reload development", "Mounts ./src and ./main.py read-only; FLASK_DEBUG=1; FLASK_ENV=development"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(profiles)]
    story.append(make_table(rows, [2*cm, 2.5*cm, 4*cm, 8.5*cm]))

    story.append(sp())
    story.append(h2("Volume Strategy"))
    story.append(p(
        "A named Docker volume (<code>streamfind-data</code>) is mounted to <code>/app/data</code> "
        "where SQLite writes its database file. This means the database persists across container "
        "restarts and image upgrades without bind-mounting the host filesystem — consistent "
        "behaviour across developer machines and CI environments."
    ))
    story.append(PageBreak())

# ── Section 14: Testing ───────────────────────────────────────────────────────
def section_testing(story):
    story.append(h1("14. Testing Strategy"))
    story.append(p(
        "The test suite uses <b>pytest</b> with an in-memory SQLite fixture (<code>conftest.py</code>). "
        "The <code>db_session</code> fixture creates all tables and seeds default preferences "
        "in a fresh in-memory database for every test, ensuring full isolation."
    ))

    files = [
        ["Test file", "Scope", "Notable patterns"],
        ["test_db.py", "ORM models, init_db()", "Checks table creation, preference seeding, JSON serialisation helpers, UserTag unique constraint."],
        ["test_repositories.py", "All repository functions", "Tests CRUD, TTL staleness logic, tag mutual exclusivity, get_tags_for_shows() dict shape."],
        ["test_rating_service.py", "normalize_ratings(), compute_weighted_rating(), sort_shows()", "Pure function tests — no DB; 3 test classes, 16 test cases covering edge cases (None values, zero weights, single source)."],
        ["test_recommendation_engine.py", "TF-IDF build, train(), recommend()", "Uses in-memory session with seeded ShowCache rows; verifies 3-like threshold, tag exclusion, score range."],
        ["test_api_routes.py", "Flask routes /api/search, /api/tag", "Flask test client; mocks StreamingAPIClient to avoid real HTTP; verifies response contract ({shows, next_cursor, has_more})."],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(files)]
    story.append(make_table(rows, [4.5*cm, 3.5*cm, 9*cm]))

    story.append(sp())
    story.append(h2("What Is NOT Tested (Documented Gaps)"))
    story += bullets([
        "Flask template rendering — templates are tested implicitly via visual review.",
        "rate_client.py API calls — external HTTP is not mocked in unit tests; integration tested manually.",
        "CLI interaction — cli.py uses stdin; requires manual or E2E testing.",
        "Docker healthcheck behaviour — tested via docker-compose health status in deployment.",
    ])
    story.append(PageBreak())

# ── Section 15: Design decisions ─────────────────────────────────────────────
def section_decisions(story):
    story.append(h1("15. Key Design Decisions & Trade-offs"))

    decisions = [
        {
            "title": "Repository Pattern over inline queries",
            "decision": "All DB access through repositories.py only",
            "benefit": "Single test seam; backend change requires touching one file",
            "tradeoff": "More indirection for simple reads",
        },
        {
            "title": "SQLite + SQLAlchemy ORM",
            "decision": "No raw SQL; SQLite for single-user simplicity",
            "benefit": "Zero-config deployment; migration to Postgres is add user_id FK only",
            "tradeoff": "Not suitable for concurrent writes at scale",
        },
        {
            "title": "Vanilla JavaScript",
            "decision": "No framework; three module files only",
            "benefit": "No build step; no dependency churn; loads instantly",
            "tradeoff": "No type checking; manual DOM manipulation is verbose vs React",
        },
        {
            "title": "TF-IDF over collaborative filtering",
            "decision": "Content-based ML using genres/countries/decade",
            "benefit": "Works with a single user; no user-to-user matrix needed",
            "tradeoff": "Cannot discover cross-genre surprises; limited to content similarity",
        },
        {
            "title": "Cursor-based pagination",
            "decision": "Pass cursor token from API response to next request",
            "benefit": "Stable across insertions; no offset drift; matches RapidAPI native model",
            "tradeoff": "Cannot jump to arbitrary page; cursor stack needed for back-navigation",
        },
        {
            "title": "Optimistic UI for tags",
            "decision": "Toggle button class before server confirms",
            "benefit": "Instant perceived response; better UX on slow connections",
            "tradeoff": "Brief inconsistency on network failure (reverted after ~1 s)",
        },
        {
            "title": "Single-user now, multi-user migration path documented",
            "decision": "No user_id in schema; migration path in CLAUDE.md",
            "benefit": "Simpler codebase; no auth overhead for personal use",
            "tradeoff": "Adding multi-user requires a DB migration and scoping all repo functions",
        },
        {
            "title": "7-day rating cache TTL",
            "decision": "Cache OMDB/TMDB results for 7 days per show",
            "benefit": "Stays within free-tier rate limits; fast repeat searches",
            "tradeoff": "Ratings up to 7 days stale; Rotten Tomatoes scores can shift for new releases",
        },
    ]

    for d in decisions:
        story.append(h3(d["title"]))
        data = [
            [cell("Decision", bold=True), cell(d["decision"])],
            [cell("Benefit",  bold=True), cell(d["benefit"])],
            [cell("Trade-off",bold=True), cell(d["tradeoff"])],
        ]
        story.append(Table(data, colWidths=[3*cm, 14*cm],
            style=TableStyle([
                ("ROWBACKGROUNDS", (0,0), (-1,-1), [LIGHT_GRAY, WHITE, colors.HexColor("#fff0ee")]),
                ("GRID",  (0,0), (-1,-1), 0.3, MID_GRAY),
                ("TOPPADDING",    (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ("LEFTPADDING",   (0,0), (-1,-1), 6),
                ("RIGHTPADDING",  (0,0), (-1,-1), 6),
            ])))
        story.append(sp(0.15))
    story.append(PageBreak())

# ── Section 16: Data flows ────────────────────────────────────────────────────
def section_flows(story):
    story.append(h1("16. Data Flow Walkthroughs"))

    story.append(h2("16.1 Search & Results"))
    steps = [
        ("1", "User submits filter form in browser"),
        ("2", "search.js serialises form → POST /api/search"),
        ("3", "Flask route parses body; detects title vs filter search"),
        ("4", "StreamingAPIClient.fetch_single_page() → RapidAPI HTTP GET"),
        ("5", "Response: list of raw show dicts + next_cursor + has_more"),
        ("6", "batch_enrich(): check cache → MDBList / OMDB / TMDB as needed → upsert_show_cache()"),
        ("7", "apply_weighted_rating(): normalise → weighted average"),
        ("8", "get_tags_for_shows(): single DB query → {imdb_id: [tags]}"),
        ("9", "JSON response: {shows, next_cursor, has_more}"),
        ("10", "search.js: renderResults() → buildCard() per show → DOM insert"),
    ]
    for n, t in steps:
        story.append(Paragraph(f"<b>{n}.</b> &nbsp;{t}", BULLET))
    story.append(sp())

    story.append(h2("16.2 Tagging a Show"))
    steps2 = [
        ("1", "User clicks ♥ on card"),
        ("2", "tags.js: optimistically sets .tag-active class + removes opposing tag class"),
        ("3", "Fetch POST /api/tag {imdb_id, tag:'liked', title, poster_url}"),
        ("4", "Flask: repositories.upsert_tag() — deletes any existing 'disliked' row, inserts 'liked'"),
        ("5", "SQLAlchemy commit; 200 OK returned"),
        ("6", "On error: catch block reverts DOM class changes"),
    ]
    for n, t in steps2:
        story.append(Paragraph(f"<b>{n}.</b> &nbsp;{t}", BULLET))
    story.append(sp())

    story.append(h2("16.3 Generating Recommendations"))
    steps3 = [
        ("1", "User visits /recommendations page"),
        ("2", "Flask checks: len(liked_ids) >= 3"),
        ("3", "get_or_rebuild_recommendations(): compare cache timestamp vs 24h + compare based_on_tags vs current liked_ids"),
        ("4", "If stale: recommendation_engine.train(all_cached_shows) → TF-IDF matrix"),
        ("5", "recommend(liked_ids, disliked_ids): avg(liked vectors) − 0.5×avg(disliked vectors) → cosine similarity all rows"),
        ("6", "Exclude already-tagged shows; keep top 20 scores > 0"),
        ("7", "write_recommendations_cache(): truncate + insert new rows"),
        ("8", "Template renders cards with similarity % badge"),
    ]
    for n, t in steps3:
        story.append(Paragraph(f"<b>{n}.</b> &nbsp;{t}", BULLET))
    story.append(sp())

    story.append(h2("16.4 Updating Rating Weights"))
    steps4 = [
        ("1", "User adjusts IMDB slider to 0.4 in settings panel"),
        ("2", "ratings.js: input event → updates ratingWeights.imdb = 0.4 → displays '40%' label → auto-switches to 'Custom' profile"),
        ("3", "User clicks Save & Apply"),
        ("4", "PUT /api/preferences {rating_weights: {...}, visible_ratings: [...]}"),
        ("5", "Flask: repositories.set_preference('rating_weights', ...) + set_preference('visible_ratings', ...)"),
        ("6", "Next search: web_ui reads preferences → passes weights to apply_weighted_rating()"),
    ]
    for n, t in steps4:
        story.append(Paragraph(f"<b>{n}.</b> &nbsp;{t}", BULLET))
    story.append(PageBreak())

# ── Section 17: Security ──────────────────────────────────────────────────────
def section_security(story):
    story.append(h1("17. Security Considerations"))

    sec = [
        ["Concern", "Mitigation", "Confidence"],
        ["API key exposure", "Keys in .env only; never committed to code; Docker injects at runtime", "High"],
        ["SQL injection", "SQLAlchemy ORM — no raw SQL strings anywhere in the codebase", "High"],
        ["XSS (stored)", "Jinja2 auto-escapes all template variables by default; JS uses textContent/innerHTML with escaped attributes", "High"],
        ["CSRF", "No session cookies; API routes accept JSON (not form-encoded); no state-changing GET routes", "High"],
        ["Container privilege escalation", "Dockerfile creates non-root appuser; process runs without root", "High"],
        ["Rate limiting", "Handled at API-provider level; no DoS risk to app itself for single-user deployment", "Medium"],
        ["Dependency vulnerabilities", "requirements.txt pins major versions; pip audit recommended before production deploy", "Medium"],
        ["Data privacy", "All data local (SQLite file); no third-party analytics; show data only", "High"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(sec)]
    story.append(make_table(rows, [5*cm, 9*cm, 3*cm]))
    story.append(PageBreak())

# ── Section 18: Roadmap ───────────────────────────────────────────────────────
def section_roadmap(story):
    story.append(h1("18. Future Roadmap"))

    story.append(h2("Phase 1 — Foundation (Complete ✓)"))
    story += bullets([
        "SQLite + SQLAlchemy persistence",
        "OMDB + TMDB rating enrichment",
        "Weighted rating computation",
        "Production country filter",
        "Advanced sort options",
        "Rating chips UI + weight sliders",
        "Templates and static assets extracted",
    ])

    story.append(h2("Phase 2 — Tag System (Complete ✓)"))
    story += bullets([
        "Like / dislike / watchlist tags",
        "Watchlist page",
        "Tag UI on cards with optimistic updates",
    ])

    story.append(h2("Phase 3 — ML Recommendations (Complete ✓)"))
    story += bullets([
        "TF-IDF content-based recommendations",
        "Recommendations page",
        "Cache invalidation on liked set change",
    ])

    story.append(h2("Potential Phase 4 — Multi-User"))
    story.append(p(
        "The architecture is explicitly designed for a one-migration multi-user upgrade path:"
    ))
    story += bullets([
        "Add <b>users</b> table: id, username, email, created_at",
        "Add <b>user_id</b> FK to user_tags and user_preferences",
        "Add session/auth middleware (Flask-Login or JWT)",
        "Scope all repository functions to accept user_id param",
        "No other architectural changes needed — the ORM, repository, and route layers are already modular",
    ])

    story.append(h2("Other Potential Improvements"))
    story += bullets([
        "<b>Async enrichment</b>: Use asyncio + aiohttp for concurrent OMDB/TMDB calls instead of sequential requests.",
        "<b>Better ML features</b>: Incorporate show overview text via TF-IDF on plot summaries for richer similarity.",
        "<b>Export/Import</b>: Let users export their tags as JSON for backup or migration.",
        "<b>Notifications</b>: Webhook or email alerts when a watchlist title becomes available on a new service.",
        "<b>Playwright E2E tests</b>: Cover the search → tag → recommendations happy path end-to-end.",
    ])
    story.append(PageBreak())

# ── Appendix: File map ────────────────────────────────────────────────────────
def appendix(story):
    story.append(h1("Appendix — Complete File Map"))
    files = [
        ["File", "Lines (approx.)", "Responsibility"],
        ["main.py", "99", "Entry point: CLI args, --init-db, launches Flask or CLI"],
        ["src/config.py", "305", "APIConfig, SearchParams, RatingConfig, AppConfig dataclasses"],
        ["src/api_client.py", "331", "StreamingAPIClient, Show, FetchResult — RapidAPI wrapper"],
        ["src/db.py", "164", "SQLAlchemy engine, ORM models, init_db(), get_session()"],
        ["src/repositories.py", "197", "ALL database access — every query lives here"],
        ["src/rating_client.py", "307", "MdblistClient, OmdbClient, TmdbClient, batch_enrich()"],
        ["src/rating_service.py", "121", "normalize_ratings(), compute_weighted_rating() — pure functions"],
        ["src/recommendation_engine.py", "198", "TF-IDF model: build_feature_string(), train(), recommend()"],
        ["src/web_ui.py", "450", "Flask app: all routes, Jinja2 templates"],
        ["src/cli.py", "310", "Interactive terminal interface"],
        ["templates/base.html", "40", "Base layout: nav, CSS/JS imports"],
        ["templates/index.html", "184", "Search results grid + filter bar + settings panel"],
        ["templates/watchlist.html", "83", "Watchlist view with remove buttons"],
        ["templates/recommendations.html", "99", "ML recommendations view with similarity badges"],
        ["static/css/main.css", "713", "All base styles: nav, cards, grid, skeleton, chips"],
        ["static/css/tags.css", "85", "Tag badge and icon button styles"],
        ["static/js/search.js", "242", "Search, pagination, card rendering, sessionStorage state"],
        ["static/js/ratings.js", "222", "Weight sliders, visible-rating toggles, profile presets"],
        ["static/js/tags.js", "80", "Tag buttons: optimistic UI, POST/DELETE /api/tag"],
        ["Dockerfile", "65", "Multi-stage build, non-root user, healthcheck"],
        ["docker-compose.yml", "127", "web / cli / dev service profiles, named volume"],
        ["requirements.txt", "20", "8 core Python dependencies"],
        ["tests/conftest.py", "32", "Shared db_session fixture (in-memory SQLite)"],
        ["tests/test_db.py", "57", "ORM model and init_db() tests"],
        ["tests/test_repositories.py", "141", "All repository function tests"],
        ["tests/test_rating_service.py", "119", "Rating normalisation, weighted scoring, sorting"],
        ["tests/test_recommendation_engine.py", "107", "TF-IDF feature building and recommendation tests"],
        ["tests/test_api_routes.py", "110", "Flask route contract tests"],
    ]
    rows = [[cell(c, bold=(i==0)) for c in r] for i,r in enumerate(files)]
    story.append(make_table(rows, [7*cm, 3*cm, 7*cm]))

# ── Build PDF ──────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="StreamFind Technical Report",
        author="StreamFind",
    )

    story = []
    cover(story)
    toc(story)
    section_overview(story)
    section_architecture(story)
    section_tech(story)
    section_main(story)
    section_config(story)
    section_api_client(story)
    section_db(story)
    section_rating(story)
    section_ml(story)
    section_webui(story)
    section_cli(story)
    section_frontend(story)
    section_docker(story)
    section_testing(story)
    section_decisions(story)
    section_flows(story)
    section_security(story)
    section_roadmap(story)
    appendix(story)

    doc.build(story)
    print(f"✓ Report written to {OUTPUT}")

if __name__ == "__main__":
    build()
