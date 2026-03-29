/**
 * tags.js — Tag button UI with optimistic updates
 * Provides buildTagButtons() used by search.js
 */

function buildTagButtons(imdbId, title, posterUrl, activeTags) {
    activeTags = activeTags || [];
    const likeActive      = activeTags.includes('liked')     ? 'tag-active' : '';
    const dislikeActive   = activeTags.includes('disliked')  ? 'tag-active' : '';
    const watchlistActive = activeTags.includes('watchlist') ? 'tag-active' : '';

    const safe = (str) => (str || '').replace(/"/g, '&quot;');

    return `
        <div class="card-tags">
            <button class="tag-btn tag-like ${likeActive}"
                    data-imdb-id="${imdbId}"
                    data-title="${safe(title)}"
                    data-poster="${safe(posterUrl)}"
                    title="Like"
                    onclick="handleTagClick(event, 'liked')">♥</button>
            <button class="tag-btn tag-dislike ${dislikeActive}"
                    data-imdb-id="${imdbId}"
                    data-title="${safe(title)}"
                    data-poster="${safe(posterUrl)}"
                    title="Dislike"
                    onclick="handleTagClick(event, 'disliked')">✕</button>
            <button class="tag-btn tag-watchlist ${watchlistActive}"
                    data-imdb-id="${imdbId}"
                    data-title="${safe(title)}"
                    data-poster="${safe(posterUrl)}"
                    title="Add to Watchlist"
                    onclick="handleTagClick(event, 'watchlist')">⊕</button>
        </div>`;
}

async function handleTagClick(event, tag) {
    event.stopPropagation();
    const btn    = event.currentTarget;
    const imdbId = btn.dataset.imdbId;
    const title  = btn.dataset.title;
    const poster = btn.dataset.poster;

    const wasActive = btn.classList.contains('tag-active');

    // Optimistic update
    btn.classList.toggle('tag-active');

    // liked/disliked are mutually exclusive
    if (tag === 'liked' && !wasActive) {
        const dislikeBtn = btn.closest('.card-tags')?.querySelector('.tag-dislike');
        if (dislikeBtn) dislikeBtn.classList.remove('tag-active');
    } else if (tag === 'disliked' && !wasActive) {
        const likeBtn = btn.closest('.card-tags')?.querySelector('.tag-like');
        if (likeBtn) likeBtn.classList.remove('tag-active');
    }

    try {
        if (wasActive) {
            await fetch(`/api/tag/${encodeURIComponent(imdbId)}/${tag}`, { method: 'DELETE' });
        } else {
            await fetch('/api/tag', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ imdb_id: imdbId, tag, title, poster_url: poster }),
            });
        }
    } catch {
        // Revert optimistic update on error
        btn.classList.toggle('tag-active');
        if (tag === 'liked' && !wasActive) {
            const dislikeBtn = btn.closest('.card-tags')?.querySelector('.tag-dislike');
            if (dislikeBtn) dislikeBtn.classList.add('tag-active');
        } else if (tag === 'disliked' && !wasActive) {
            const likeBtn = btn.closest('.card-tags')?.querySelector('.tag-like');
            if (likeBtn) likeBtn.classList.add('tag-active');
        }
    }
}
