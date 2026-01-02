const TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w300';
const PLACEHOLDER = 'https://via.placeholder.com/300x450?text=No+Image';

function el(id) { return document.getElementById(id); }

let currentPage = 1;
const PAGE_SIZE = 24;
let currentQuery = { actor: '', industry: '', genre: '' };

function imgFor(poster_path) {
  return poster_path ? `${TMDB_IMAGE_BASE}${poster_path}` : PLACEHOLDER;
}

function createMovieCard(m) {
  const col = document.createElement('div');
  col.className = 'col-6 col-sm-4 col-md-3 col-lg-2';

  const card = document.createElement('div');
  card.className = 'movie-card';
  card.dataset.movieId = m.id;

  const img = document.createElement('img');
  img.alt = m.title || '';
  img.src = imgFor(m.poster_path);
  img.onerror = () => img.src = PLACEHOLDER;

  const b = document.createElement('div');
  b.className = 'movie-body';
  b.innerHTML = `<p class="movie-title">${m.title}</p><p class="movie-meta">${m.release_date || ''}</p>`;

  card.appendChild(img);
  card.appendChild(b);
  col.appendChild(card);

  // click -> open detail
  card.addEventListener('click', () => openDetail(m.id));

  return col;
}

async function fetchMovies(page=1, append=false) {
  const status = el('status');
  const moviesEl = el('movies');
  status.textContent = 'Loading...';
  if (!append) moviesEl.innerHTML = '';

  try {
    const params = new URLSearchParams();
    if (currentQuery.actor) params.set('actor', currentQuery.actor);
    if (currentQuery.industry) params.set('industry', currentQuery.industry);
    if (currentQuery.genre) params.set('genre', currentQuery.genre);
    params.set('page', page);
    params.set('page_size', PAGE_SIZE);

    const res = await fetch('/api/movies/?' + params.toString());
    if (!res.ok) throw new Error('Network response was not ok');
    const movies = await res.json();
    if (!movies.length) {
      if (!append) status.textContent = 'No movies found.';
      else status.textContent = 'No more movies.';
      return;
    }

    status.textContent = '';
    for (const m of movies) {
      moviesEl.appendChild(createMovieCard(m));
    }

    // show/hide load more and spinner
    const hasMore = movies.length >= PAGE_SIZE;
    el('load-more').style.display = hasMore ? 'inline-block' : 'none';
    el('spinner').classList.add('d-none');
    loading = false;

    // if we have infinite observer, unobserve when no more
    if (!hasMore && observer) observer.disconnect();
  } catch (err) {
    console.error(err);
    status.textContent = 'Failed to load movies.';
    el('spinner').classList.add('d-none');
    loading = false;
  }
}

let loading = false;
let observer = null;

// infinite scroll: observe sentinel and auto-load next page
function attachInfiniteScroll() {
  const sentinel = el('scroll-sentinel');
  if (!sentinel) return;
  if (observer) observer.disconnect();
  observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting && !loading && el('load-more').style.display !== 'none') {
        loading = true;
        el('spinner').classList.remove('d-none');
        currentPage += 1;
        fetchMovies(currentPage, true);
      }
    }
  }, { root: null, rootMargin: '200px', threshold: 0.1 });
  observer.observe(sentinel);
}

async function openDetail(id) {
  const res = await fetch(`/api/movies/${id}/`);
  if (!res.ok) return alert('Failed to load movie');
  const m = await res.json();

  const titleEl = el('modal-title');
  const bodyEl = el('modal-body-content');
  titleEl.textContent = m.title;
  bodyEl.innerHTML = `
    <div class="row">
      <div class="col-md-4"><img src="${imgFor(m.poster_path)}" alt="${m.title}" class="img-fluid" onerror="this.src='${PLACEHOLDER}'"></div>
      <div class="col-md-8">
        <p>${m.overview || ''}</p>
        <p><strong>Genres:</strong> ${m.genres.map(g => g.name).join(', ')}</p>
        <p><strong>Cast:</strong> ${m.cast.map(c => c.name).join(', ')}</p>
        <p><strong>Availability:</strong> ${m.availabilities.map(a => `<a href='${a.url || '#'}' target='_blank'>${a.platform}</a>`).join(', ')}</p>
        <p><strong>Watch on YouTube:</strong> ${m.youtube_links.map(y => `<a href='${y.url}' target='_blank'>${y.title || y.url}</a>`).join(', ')}</p>
      </div>
    </div>
  `;

  const modal = new bootstrap.Modal(document.getElementById('movieModal'));
  modal.show();
}

// show details for an external TMDB-only result (no DB id)
async function openExternalDetail(tmdbId) {
  const apiKey = null; // server will fetch full details instead for consistency
  const res = await fetch(`/api/external-search/?q=${encodeURIComponent(tmdbId)}`);
  // The external-search endpoint expects text, but for TMDB movie details we can call the movie detail endpoint directly on TMDB.
  // Simpler: call TMDB movie details via our server by adding a small helper endpoint. For now, open TMDB page in new tab.
  const tmdbUrl = `https://www.themoviedb.org/movie/${tmdbId}`;
  window.open(tmdbUrl, '_blank');
}

async function loadFilters() {
  // genres
  try {
    const g = await fetch('/api/genres/').then(r => r.json());
    const gs = el('q-genre');
    const bestg = el('best-genre');
    g.forEach(x => {
      const opt = document.createElement('option'); opt.value = x.name; opt.textContent = x.name; gs.appendChild(opt);
      const opt2 = document.createElement('option'); opt2.value = x.name; opt2.textContent = x.name; bestg.appendChild(opt2);
    });
  } catch (e) { console.warn('Failed to load genres', e); }

  try {
    const is = await fetch('/api/industries/').then(r => r.json());
    const sel = el('q-industry');
    is.forEach(x => { const opt = document.createElement('option'); opt.value = x.name; opt.textContent = x.name; sel.appendChild(opt); });
  } catch (e) { console.warn('Failed to load industries', e); }
}

async function getBest() {
  const genre = el('best-genre').value;
  if (!genre) return alert('Choose a genre');
  const res = await fetch(`/api/best/?genre=${encodeURIComponent(genre)}`);
  if (!res.ok) return alert('Not found');
  const m = await res.json();
  const out = el('best-result');
  out.innerHTML = '';
  out.appendChild(createMovieCard(m));
}

async function recommend() {
  const genres = el('rec-genres').value;
  const actors = el('rec-actors').value;
  const params = new URLSearchParams();
  if (genres) params.set('genres', genres);
  if (actors) params.set('actors', actors);
  const res = await fetch('/api/recommend/?' + params.toString());
  if (!res.ok) return alert('Failed to get recommendations');
  const list = await res.json();
  const out = el('rec-results'); out.innerHTML = '';
  list.forEach(m => out.appendChild(createMovieCard(m)));
}

// wire up events
document.addEventListener('DOMContentLoaded', () => {
  loadFilters();
  fetchMovies(1, false);

  el('refresh').addEventListener('click', () => { currentPage = 1; fetchMovies(1, false); });
  el('btn-search').addEventListener('click', async () => {
    currentQuery.title = el('q-title').value.trim();
    currentQuery.actor = el('q-actor').value.trim();
    currentQuery.industry = el('q-industry').value.trim();
    currentQuery.genre = el('q-genre').value.trim();
    currentPage = 1;
    await fetchMovies(1, false);

    // If no results and user searched a title, fall back to external TMDB search
    const statusText = el('status').textContent || '';
    const moviesEl = el('movies');
    if ((moviesEl.children.length === 0 || statusText.includes('No movies')) && currentQuery.title) {
      // call external search
      try {
        const res = await fetch('/api/external-search/?q=' + encodeURIComponent(currentQuery.title));
        if (res.ok) {
          const list = await res.json();
          if (list && list.length) {
            el('status').textContent = 'Showing external search results (from TMDB) — click a card to view details.';
            moviesEl.innerHTML = '';
            for (const m of list) {
              const col = createMovieCard(m); // createMovieCard uses fields title/poster_path/release_date
              // mark as external
              col.querySelector('.movie-card').dataset.external = 'true';
              col.querySelector('.movie-card').dataset.tmdbId = m.tmdb_id;
              // when clicked, open external detail handler
              col.querySelector('.movie-card').addEventListener('click', () => openExternalDetail(m.tmdb_id));
              moviesEl.appendChild(col);
            }
            el('load-more').style.display = 'none';
            if (observer) observer.disconnect();
          }
        }
      } catch (e) {
        console.warn('External search failed', e);
      }
    }
  });

  el('btn-clear').addEventListener('click', () => {
    el('q-actor').value = '';
    el('q-industry').value = '';
    el('q-genre').value = '';
    currentQuery = { actor: '', industry: '', genre: '' };
    currentPage = 1;
    fetchMovies(1, false);
  });

  el('load-more').addEventListener('click', () => {
    el('spinner').classList.remove('d-none');
    currentPage += 1;
    fetchMovies(currentPage, true);
  });

  el('best-btn').addEventListener('click', getBest);
  el('rec-btn').addEventListener('click', recommend);

  // attach infinite scroll after initial load
  attachInfiniteScroll();
});
