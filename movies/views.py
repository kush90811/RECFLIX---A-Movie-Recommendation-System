import requests
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render
from .models import Movie


def test_tmdb(request):
    """Return TMDB popular movies JSON (server-side uses TMDB_API_KEY)."""
    api_key = settings.TMDB_API_KEY
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    return JsonResponse(data)


def home(request):
    """Render the frontend home template and include server-side trending categories as a fallback for the UI."""
    trending = []
    # Overall trending
    trending.append({
        'title': 'Trending Now',
        'movies': Movie.objects.order_by('-popularity')[:12]
    })
    # Genre sections
    for g in ('Action', 'Comedy'):
        trending.append({
            'title': g,
            'movies': Movie.objects.filter(genres__name__iexact=g).order_by('-popularity')[:12]
        })
    # Industry sections
    for ind in ('Hollywood', 'Bollywood'):
        trending.append({
            'title': ind,
            'movies': Movie.objects.filter(industry__name__iexact=ind).order_by('-popularity')[:12]
        })

    return render(request, "movies/home.html", {'trending_categories': trending})
