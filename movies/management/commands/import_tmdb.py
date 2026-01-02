import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from movies.models import (
    Movie,
    Genre,
    Person,
    Platform,
    Availability,
    Industry,
    YouTubeLink,
)


class Command(BaseCommand):
    help = 'Import popular movies from TMDB into the database (simple loader).'

    def add_arguments(self, parser):
        parser.add_argument('--pages', type=int, default=1, help='Number of popular pages to fetch')
        parser.add_argument('--genre', type=str, help='Discover by genre name (e.g., Comedy)')
        parser.add_argument('--industry', type=str, help='Limit to industry (Bollywood/Hollywood/Tollywood)')

    def handle(self, *args, **options):
        api_key = settings.TMDB_API_KEY
        if not api_key:
            raise CommandError('TMDB_API_KEY not set in environment or .env')

        pages = options['pages']
        base = 'https://api.themoviedb.org/3'

        # If a genre is provided, discover by genre id
        genre_id = None
        if options.get('genre'):
            gens = requests.get(f"{base}/genre/movie/list?api_key={api_key}&language=en-US").json()
            name = options.get('genre').lower()
            for g in gens.get('genres', []):
                if g.get('name', '').lower() == name:
                    genre_id = g.get('id')
                    break

        # Use discover endpoint when genre or industry filter provided
        if genre_id or options.get('industry'):
            self.stdout.write('Using discover endpoint with filters...')
            for page in range(1, pages + 1):
                params = {
                    'api_key': api_key,
                    'language': 'en-US',
                    'page': page,
                }
                if genre_id:
                    params['with_genres'] = genre_id
                # industry mapping: use original_language or production_country hints later per movie
                r = requests.get(f"{base}/discover/movie", params=params)
                r.raise_for_status()
                data = r.json()
                for item in data.get('results', []):
                    tmdb_id = item.get('id')
                    try:
                        self._import_movie(tmdb_id, api_key, base, industry_hint=options.get('industry'))
                    except Exception as e:
                        self.stderr.write(f'Failed to import {tmdb_id}: {e}')
        else:
            for page in range(1, pages + 1):
                url = f"{base}/movie/popular?api_key={api_key}&language=en-US&page={page}"
                self.stdout.write(f'Fetching popular page {page}...')
                r = requests.get(url)
                r.raise_for_status()
                data = r.json()
                for item in data.get('results', []):
                    tmdb_id = item.get('id')
                    try:
                        self._import_movie(tmdb_id, api_key, base, industry_hint=options.get('industry'))
                    except Exception as e:
                        self.stderr.write(f'Failed to import {tmdb_id}: {e}')

    def _detect_industry(self, details, industry_hint=None):
        # Heuristics: production_countries, original_language
        hint = (industry_hint or '').strip().lower() if industry_hint else None
        if hint:
            return Industry.objects.get_or_create(name=hint.capitalize())[0]

        countries = [c.get('iso_3166_1') for c in details.get('production_countries', [])]
        lang = details.get('original_language')
        if 'IN' in countries or lang == 'hi' or lang == 'te' or lang == 'ta':
            # if more nuanced, map languages to industries
            # We'll treat Hindi as Bollywood, Telugu/Tamil as Tollywood
            if lang == 'hi':
                return Industry.objects.get_or_create(name='Bollywood')[0]
            if lang in ('te', 'ta'):
                return Industry.objects.get_or_create(name='Tollywood')[0]
            # fallback to Bollywood if produced in India
            return Industry.objects.get_or_create(name='Bollywood')[0]
        if 'US' in countries or lang == 'en':
            return Industry.objects.get_or_create(name='Hollywood')[0]
        return Industry.objects.get_or_create(name='Other')[0]


    def _import_movie(self, tmdb_id, api_key, base, industry_hint=None):
        videos_url = f"{base}/movie/{tmdb_id}/videos?api_key={api_key}&language=en-US"
        detail_url = f"{base}/movie/{tmdb_id}?api_key={api_key}&language=en-US"
        credits_url = f"{base}/movie/{tmdb_id}/credits?api_key={api_key}&language=en-US"
        providers_url = f"{base}/movie/{tmdb_id}/watch/providers?api_key={api_key}"

        d = requests.get(detail_url).json()
        # create or update movie
        industry_obj = self._detect_industry(d, industry_hint=industry_hint)

        movie, created = Movie.objects.update_or_create(
            tmdb_id=str(d.get('id')),
            defaults={
                'title': d.get('title') or d.get('name') or 'Untitled',
                'original_title': d.get('original_title'),
                'synopsis': d.get('overview'),
                'overview': d.get('overview'),
                'release_date': d.get('release_date') or None,
                'runtime_minutes': d.get('runtime') or None,
                'poster_path': d.get('poster_path') or '',
                'popularity': d.get('popularity') or 0.0,
                'vote_average': d.get('vote_average') or None,
                'vote_count': d.get('vote_count') or None,
                'industry': industry_obj,
            }
        )

        # genres
        for g in d.get('genres', []):
            genre, _ = Genre.objects.get_or_create(name=g.get('name'))
            movie.genres.add(genre)

        # credits -> top 5 cast
        c = requests.get(credits_url).json()
        for actor in c.get('cast', [])[:5]:
            p, _ = Person.objects.get_or_create(name=actor.get('name'))
            movie.cast.add(p)

        # providers (select country 'US' or fallback first)
        p = requests.get(providers_url).json()
        results = p.get('results') or {}
        provider_info = results.get('US') or next(iter(results.values())) if results else None
        if provider_info:
            flatrates = provider_info.get('flatrate') or []
            for prov in flatrates:
                platform, _ = Platform.objects.get_or_create(name=prov.get('provider_name'))
                Availability.objects.update_or_create(movie=movie, platform=platform, defaults={'is_available': True})

        # videos -> YouTube links
        v = requests.get(videos_url).json()
        for vid in v.get('results', []):
            site = vid.get('site')
            key = vid.get('key')
            if site == 'YouTube' and key:
                url = f'https://www.youtube.com/watch?v={key}'
                YouTubeLink.objects.update_or_create(movie=movie, url=url, defaults={'title': vid.get('name'), 'is_official': True})

        movie.save()
        self.stdout.write(self.style.SUCCESS(f'Imported: {movie.title} ({movie.tmdb_id})'))
