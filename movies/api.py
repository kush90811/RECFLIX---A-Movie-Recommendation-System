from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .models import Movie, Genre, Person, Industry
from .serializers import MovieSerializer, GenreSerializer, IndustrySerializer


class MovieListAPI(generics.ListAPIView):
    serializer_class = MovieSerializer

    def get_queryset(self):
        qs = Movie.objects.all()
        q = self.request.query_params
        industry = q.get('industry')
        genre = q.get('genre')
        actor = q.get('actor')
        if industry:
            qs = qs.filter(industry__name__iexact=industry)
        if genre:
            qs = qs.filter(genres__name__iexact=genre)
        if actor:
            qs = qs.filter(cast__name__icontains=actor)

        # text search
        qtext = self.request.query_params.get('q')
        if qtext:
            qs = qs.filter(
                Q(title__icontains=qtext) |
                Q(original_title__icontains=qtext) |
                Q(overview__icontains=qtext)
            )

        qs = qs.distinct()
        # simple pagination support via query params
        page = int(self.request.query_params.get('page') or 1)
        page_size = int(self.request.query_params.get('page_size') or 24)
        start = (page - 1) * page_size
        end = start + page_size
        return qs[start:end]


class MovieDetailAPI(generics.RetrieveAPIView):
    serializer_class = MovieSerializer
    queryset = Movie.objects.all()


class GenreListAPI(generics.ListAPIView):
    serializer_class = GenreSerializer
    queryset = Genre.objects.all()


class IndustryListAPI(generics.ListAPIView):
    serializer_class = IndustrySerializer
    queryset = Industry.objects.all()


class BestInGenreAPI(APIView):
    """Return the single best movie for a given genre (based on vote_average & popularity)."""

    def get(self, request):
        genre = request.query_params.get('genre')
        if not genre:
            return Response({'detail': 'Provide ?genre=Name'}, status=400)
        try:
            g = Genre.objects.get(name__iexact=genre)
        except Genre.DoesNotExist:
            return Response({'detail': 'Genre not found'}, status=404)

        movie = Movie.objects.filter(genres=g).order_by('-vote_average', '-popularity').first()
        if not movie:
            return Response({'detail': 'No movie found for that genre'}, status=404)
        return Response(MovieSerializer(movie).data)


class RecommendAPI(APIView):
    """Simple content-based recommender: accepts ?genres=Comedy,Drama&actors=Name"""

    def get(self, request):
        genres = request.query_params.get('genres')
        actors = request.query_params.get('actors')
        qs = Movie.objects.all()
        if genres:
            names = [g.strip() for g in genres.split(',')]
            qs = qs.filter(genres__name__in=names)
        if actors:
            names = [a.strip() for a in actors.split(',')]
            qobj = Q()
            for n in names:
                qobj |= Q(cast__name__icontains=n)
            qs = qs.filter(qobj)

        qs = qs.distinct().order_by('-vote_average', '-popularity')[:20]
        return Response(MovieSerializer(qs, many=True).data)


class ExternalSearchAPI(APIView):
    """Search TMDB directly and return simplified movie objects when local DB has no match.

    Response items: {"external": true, "tmdb_id": <id>, "title": ..., "poster_path": ..., "release_date": ..., "overview": ...}
    """

    def get(self, request):
        q = request.query_params.get('q')
        if not q:
            return Response({'detail': 'Provide ?q=search-term'}, status=400)
        api_key = getattr(__import__('django.conf').conf.settings, 'TMDB_API_KEY', None)
        if not api_key:
            return Response({'detail': 'TMDB_API_KEY not configured'}, status=500)
        url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&language=en-US&query={q}'
        import requests
        r = requests.get(url)
        if r.status_code != 200:
            return Response({'detail': 'TMDB error'}, status=502)
        data = r.json()
        out = []
        for item in data.get('results', []):
            out.append({
                'external': True,
                'tmdb_id': item.get('id'),
                'title': item.get('title') or item.get('name'),
                'poster_path': item.get('poster_path'),
                'release_date': item.get('release_date'),
                'overview': item.get('overview'),
            })
        return Response(out)


class TrendingAPI(APIView):
    """Return top movies ordered by popularity for a given genre or industry.

    Query params: ?genre=Action&industry=Bollywood&limit=12&type=popular|top_rated
    """

    def get(self, request):
        genre = request.query_params.get('genre')
        industry = request.query_params.get('industry')
        limit = int(request.query_params.get('limit') or 12)
        sort_type = request.query_params.get('type') or 'popular'

        qs = Movie.objects.all()
        if genre:
            qs = qs.filter(genres__name__iexact=genre)
        if industry:
            qs = qs.filter(industry__name__iexact=industry)

        if sort_type == 'top_rated':
            qs = qs.order_by('-vote_average', '-popularity')
        else:
            qs = qs.order_by('-popularity', '-vote_average')

        qs = qs.distinct()[:limit]
        return Response(MovieSerializer(qs, many=True).data)

