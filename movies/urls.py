from django.urls import path
from . import views
from . import api

urlpatterns = [
    path("", views.home, name="movies-home"),      # /api/ -> render UI
    path("tmdb/", views.test_tmdb, name="tmdb"),   # /api/tmdb/ -> TMDB JSON
]
# API endpoints under /api/
urlpatterns += [
    path('movies/', api.MovieListAPI.as_view(), name='api-movies-list'),  # /api/movies/?genre=&industry=
    path('movies/<int:pk>/', api.MovieDetailAPI.as_view(), name='api-movie-detail'),
    path('best/', api.BestInGenreAPI.as_view(), name='api-best-in-genre'),
    path('recommend/', api.RecommendAPI.as_view(), name='api-recommend'),
    path('genres/', api.GenreListAPI.as_view(), name='api-genres'),
    path('industries/', api.IndustryListAPI.as_view(), name='api-industries'),
    path('external-search/', api.ExternalSearchAPI.as_view(), name='api-external-search'),
]
