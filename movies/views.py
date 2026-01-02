import requests
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render


def test_tmdb(request):
    """Return TMDB popular movies JSON (server-side uses TMDB_API_KEY)."""
    api_key = settings.TMDB_API_KEY
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    return JsonResponse(data)


def home(request):
    """Render the frontend home template which consumes the `/api/tmdb/` endpoint."""
    return render(request, "movies/home.html")
