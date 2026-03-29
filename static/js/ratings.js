/**
 * ratings.js — Weight sliders, visible-rating toggles, settings panel, profiles
 * Must be loaded before search.js on pages that render cards.
 */

// ── Rating profiles ────────────────────────────────────
// Critic sources: rt_critics, metacritic
// Audience sources: imdb, rt_audience, tmdb
// Other: streaming

const RATING_PROFILES = {
    critically_acclaimed: {
        label: 'Critics',
        weights: { rt_critics: 0.40, metacritic: 0.40, imdb: 0.10, rt_audience: 0.05, tmdb: 0.05, streaming: 0.00 },
    },
    crowd_pleaser: {
        label: 'Audience',
        weights: { imdb: 0.35, rt_audience: 0.35, tmdb: 0.20, rt_critics: 0.05, metacritic: 0.05, streaming: 0.00 },
    },
    balanced: {
        label: 'Balanced',
        weights: { rt_critics: 0.20, metacritic: 0.20, imdb: 0.20, rt_audience: 0.20, tmdb: 0.15, streaming: 0.05 },
    },
    custom: { label: 'Custom', weights: null },
};

let activeProfile = 'custom';

// Current preferences (loaded from server on init)
let ratingWeights   = { imdb: 0.25, rt_critics: 0.2, rt_audience: 0.2, metacritic: 0.15, tmdb: 0.1, streaming: 0.1 };
let visibleRatings  = ['imdb', 'rt_critics', 'rt_audience', 'metacritic', 'tmdb'];

const RATING_LABELS = {
    imdb:       'IMDB',
    rt_critics: 'RT♥',
    rt_audience:'RT👥',
    metacritic: 'MC',
    tmdb:       'TMDB',
    weighted:   'Score',
};

const CHIP_CLASSES = {
    imdb:       'rating-chip-imdb',
    rt_critics: 'rating-chip-rt-critics',
    rt_audience:'rating-chip-rt-audience',
    metacritic: 'rating-chip-metacritic',
    tmdb:       'rating-chip-tmdb',
    weighted:   'rating-chip-weighted',
};

// ── Build rating chips for a show dict ────────────────

function buildRatingChips(show) {
    const chips = [];

    const fieldMap = {
        imdb:       show.rating_imdb != null ? parseFloat(show.rating_imdb).toFixed(1) : null,
        rt_critics: show.rating_rt_critics != null ? show.rating_rt_critics + '%' : null,
        rt_audience:show.rating_rt_audience != null ? show.rating_rt_audience + '%' : null,
        metacritic: show.rating_metacritic != null ? show.rating_metacritic : null,
        tmdb:       show.rating_tmdb != null ? parseFloat(show.rating_tmdb).toFixed(1) : null,
    };

    for (const source of visibleRatings) {
        const val = fieldMap[source];
        if (val == null) continue;
        const label = RATING_LABELS[source] || source;
        chips.push(`<span class="rating-chip ${CHIP_CLASSES[source] || ''}" title="${label}">${label} ${val}</span>`);
    }

    return chips.length > 0
        ? `<div class="rating-chips">${chips.join('')}</div>`
        : '';
}

// ── Settings panel ────────────────────────────────────

const settingsToggle = document.getElementById('settingsToggle');
const settingsPanel  = document.getElementById('settingsPanel');
const saveSettingsBtn = document.getElementById('saveSettings');

async function loadPreferences() {
    try {
        const res  = await fetch('/api/preferences');
        const data = await res.json();
        if (data.rating_weights) ratingWeights  = data.rating_weights;
        if (data.visible_ratings) visibleRatings = data.visible_ratings;
        syncSlidersToState();
        syncTogglesToState();
    } catch {
        // Use defaults if preferences endpoint not yet available
    }
}

function syncSlidersToState() {
    for (const [key, val] of Object.entries(ratingWeights)) {
        const slider = document.getElementById('w-' + key);
        const display = document.getElementById('wv-' + key);
        if (slider) slider.value = val;
        if (display) display.textContent = parseFloat(val).toFixed(2);
    }

    // Detect if loaded weights match a named profile
    const matchedProfile = Object.entries(RATING_PROFILES).find(([key, profile]) => {
        if (!profile.weights) return false;
        return Object.entries(profile.weights).every(
            ([k, v]) => Math.abs((ratingWeights[k] || 0) - v) < 0.001
        );
    });

    const profileKey = matchedProfile ? matchedProfile[0] : 'custom';
    activeProfile = profileKey;
    document.querySelectorAll('.profile-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.profile === profileKey);
    });
}

function syncTogglesToState() {
    document.querySelectorAll('.rating-toggle').forEach(btn => {
        const src = btn.dataset.source;
        btn.classList.toggle('active', visibleRatings.includes(src));
    });
}

if (settingsToggle && settingsPanel) {
    settingsToggle.addEventListener('click', () => {
        settingsPanel.classList.toggle('open');
    });

    // Close panel when clicking outside
    document.addEventListener('click', (e) => {
        if (!settingsPanel.contains(e.target) && e.target !== settingsToggle) {
            settingsPanel.classList.remove('open');
        }
    });
}

// ── Profile selector ──────────────────────────────────

function applyProfile(profileKey) {
    const profile = RATING_PROFILES[profileKey];
    if (!profile) return;

    activeProfile = profileKey;

    // Highlight active profile button
    document.querySelectorAll('.profile-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.profile === profileKey);
    });

    // Update sliders if this profile has preset weights
    if (profile.weights) {
        for (const [key, val] of Object.entries(profile.weights)) {
            const slider = document.getElementById('w-' + key);
            const display = document.getElementById('wv-' + key);
            if (slider) slider.value = val;
            if (display) display.textContent = parseFloat(val).toFixed(2);
        }
        ratingWeights = { ...profile.weights };
    }
}

document.querySelectorAll('.profile-btn').forEach(btn => {
    btn.addEventListener('click', () => applyProfile(btn.dataset.profile));
});

// Slider live updates — moving a slider switches to Custom
document.querySelectorAll('.weight-slider').forEach(slider => {
    slider.addEventListener('input', () => {
        const key = slider.id.replace('w-', '');
        const display = document.getElementById('wv-' + key);
        if (display) display.textContent = parseFloat(slider.value).toFixed(2);
        ratingWeights[key] = parseFloat(slider.value);

        // Auto-switch to Custom profile when manually adjusting
        if (activeProfile !== 'custom') {
            activeProfile = 'custom';
            document.querySelectorAll('.profile-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.profile === 'custom');
            });
        }
    });
});

// Rating visibility toggles
document.querySelectorAll('.rating-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.classList.toggle('active');
        const src = btn.dataset.source;
        if (btn.classList.contains('active')) {
            if (!visibleRatings.includes(src)) visibleRatings.push(src);
        } else {
            visibleRatings = visibleRatings.filter(s => s !== src);
        }
    });
});

if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', async () => {
        // Collect weights from sliders
        const weights = {};
        document.querySelectorAll('.weight-slider').forEach(slider => {
            weights[slider.id.replace('w-', '')] = parseFloat(slider.value);
        });
        ratingWeights = weights;

        try {
            await fetch('/api/preferences', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rating_weights: weights, visible_ratings: visibleRatings }),
            });
            settingsPanel.classList.remove('open');
        } catch {
            // Silently fail — prefs are in memory
        }
    });
}

// Load preferences on page load
loadPreferences();
