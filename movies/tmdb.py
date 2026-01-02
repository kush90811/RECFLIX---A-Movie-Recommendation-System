import os
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def get_popular_movies():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    return response.json()
