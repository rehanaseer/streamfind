/**
 * search.js — Search form, pagination, card rendering
 * Depends on: ratings.js (for getVisibleRatings, buildRatingChips)
 */

const form          = document.getElementById('searchForm');
const container     = document.getElementById('resultsContainer');
const searchBtn     = document.getElementById('searchBtn');
const countChip     = document.getElementById('countChip');
const pageControls  = document.getElementById('pageControls');
const prevBtn       = document.getElementById('prevBtn');
const nextBtn       = document.getElementById('nextBtn');
const pageIndicator = document.getElementById('pageIndicator');

// Pagination state
let cursorHistory = [];
let nextCursor    = null;
let currentPage   = 1;
let lastParams    = {};

// Current tags (populated after each search from /api/tags)
let currentTags = {};

// ── Session persistence ───────────────────────────────

const SEARCH_STATE_KEY = 'streamfind_search_state';

function saveSearchState(shows, hasMore) {
    try {
        sessionStorage.setItem(SEARCH_STATE_KEY, JSON.stringify({
            params: lastParams,
            shows,
            hasMore,
            nextCursor,
            currentPage,
            cursorHistory,
        }));
    } catch {}
}

function restoreSearchState() {
    try {
        const raw = sessionStorage.getItem(SEARCH_STATE_KEY);
        if (!raw) return;
        const state = JSON.parse(raw);
        lastParams    = state.params || {};
        nextCursor    = state.nextCursor || null;
        currentPage   = state.currentPage || 1;
        cursorHistory = state.cursorHistory || [];

        // Restore form inputs
        if (form) {
            for (const [key, val] of Object.entries(lastParams)) {
                const el = form.elements[key];
                if (el) el.value = val;
            }
        }

        if (state.shows && state.shows.length > 0) {
            renderResults(state.shows, state.hasMore);
        }
    } catch {}
}

// ── Utilities ─────────────────────────────────────────

function svcClass(name) {
    const n = name.toLowerCase();
    if (n.includes('netflix'))   return 'svc-netflix';
    if (n.includes('prime'))     return 'svc-prime';
    if (n.includes('disney'))    return 'svc-disney';
    if (n.includes('hulu'))      return 'svc-hulu';
    if (n.includes('hbo'))       return 'svc-hbo';
    if (n.includes('max'))       return 'svc-max';
    if (n.includes('apple'))     return 'svc-apple';
    if (n.includes('paramount')) return 'svc-paramount';
    if (n.includes('peacock'))   return 'svc-peacock';
    return 'svc-default';
}

function buildCard(s) {
    const poster = s.poster_url
        ? `<img src="${s.poster_url}" alt="${(s.title || '').replace(/"/g,'&quot;')}" loading="lazy">`
        : `<div class="card-no-img">🎬</div>`;

    const displayRating = s.weighted_rating || s.rating;
    const ratingClass = displayRating >= 70 ? 'high' : displayRating >= 50 ? 'mid' : 'low';
    const ratingBadge = displayRating
        ? `<div class="card-rating ${ratingClass}">★ ${displayRating}</div>`
        : '';

    const svcs = (s.streaming_services || []).slice(0, 3)
        .map(sv => `<span class="svc ${svcClass(sv)}">${sv}</span>`).join('');

    const meta = [s.release_year, (s.genres || []).slice(0,2).join(' · ')]
        .filter(Boolean).join(' · ');

    // Rating chips (uses visible ratings from ratings.js)
    const ratingChips = buildRatingChips(s);

    // Tag buttons
    const tags = s.current_tags || currentTags[s.imdb_id] || [];
    const tagBtns = s.imdb_id ? buildTagButtons(s.imdb_id, s.title, s.poster_url, tags) : '';

    return `
        <div class="card">
            <div class="card-poster">
                ${poster}
                ${ratingBadge}
                ${tagBtns}
                <div class="card-overlay">
                    <div class="card-ov-title">${s.title || 'Unknown'}</div>
                    <div class="card-ov-meta">${meta}</div>
                    <div class="card-svcs">${svcs}</div>
                </div>
            </div>
            <div class="card-label">${s.title || 'Unknown'}</div>
            ${ratingChips}
        </div>`;
}

// ── States ────────────────────────────────────────────

function showSkeletons() {
    const n = 18;
    const skels = Array.from({length: n}, () =>
        `<div class="skel-card"><div class="skel-img"></div><div class="skel-label"></div></div>`
    ).join('');
    container.innerHTML = `
        <div class="shelf-wrap">
            <div class="shelf-header"><span class="shelf-title">Loading…</span></div>
            <div class="shelf-track">${skels}</div>
        </div>`;
    if (searchBtn) { searchBtn.disabled = true; searchBtn.textContent = 'Searching…'; }
    if (countChip) countChip.style.display = 'none';
    if (pageControls) pageControls.style.display = 'none';
}

function showError(msg) {
    container.innerHTML = `<div class="error-msg">${msg}</div>`;
    if (countChip) countChip.style.display = 'none';
    if (pageControls) pageControls.style.display = 'none';
}

function showEmpty() {
    container.innerHTML = `
        <div class="hero">
            <div class="hero-title" style="font-size:1.4rem">No results</div>
            <div class="hero-sub">Try adjusting your filters or switching country.</div>
        </div>`;
    if (countChip) countChip.style.display = 'none';
    if (pageControls) pageControls.style.display = 'none';
}

function renderResults(shows, hasMore) {
    if (!shows || shows.length === 0) { showEmpty(); return; }

    const cards = shows.map(buildCard).join('');

    container.innerHTML = `
        <div class="shelf-wrap">
            <div class="shelf-header">
                <span class="shelf-title">Results</span>
                <span class="shelf-count">${shows.length} titles &nbsp;·&nbsp; Page ${currentPage}</span>
            </div>
            <div class="shelf-track">${cards}</div>
        </div>`;

    saveSearchState(shows, hasMore);

    if (countChip) { countChip.textContent = shows.length + ' titles'; countChip.style.display = ''; }
    if (pageControls) {
        pageControls.style.display = '';
        pageIndicator.textContent  = 'Page ' + currentPage;
        prevBtn.disabled = currentPage <= 1;
        nextBtn.disabled = !hasMore;
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Fetch ─────────────────────────────────────────────

async function fetchPage(cursor) {
    showSkeletons();
    const params = { ...lastParams };
    if (cursor) params.cursor = cursor;

    try {
        const res  = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        const data = await res.json();

        if (data.error) {
            showError(data.error);
        } else {
            nextCursor = data.next_cursor || null;
            renderResults(data.shows, data.has_more);
        }
    } catch {
        showError('Network error — please try again.');
    } finally {
        if (searchBtn) { searchBtn.disabled = false; searchBtn.textContent = 'Search'; }
    }
}

if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        cursorHistory = [];
        nextCursor    = null;
        currentPage   = 1;
        lastParams    = Object.fromEntries(new FormData(form).entries());
        await fetchPage(null);
    });
}

if (nextBtn) {
    nextBtn.addEventListener('click', async () => {
        if (!nextCursor) return;
        cursorHistory.push(nextCursor);
        currentPage++;
        await fetchPage(nextCursor);
    });
}

// Restore previous search on page load
restoreSearchState();

if (prevBtn) {
    prevBtn.addEventListener('click', async () => {
        if (currentPage <= 1) return;
        cursorHistory.pop();
        currentPage--;
        const cursor = cursorHistory[cursorHistory.length - 1] || null;
        await fetchPage(cursor);
    });
}
