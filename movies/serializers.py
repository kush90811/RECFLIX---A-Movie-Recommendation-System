from rest_framework import serializers
from .models import Movie, Genre, Person, Platform, Availability, YouTubeLink, Industry


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name')


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ('id', 'name')


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ('id', 'name')


class AvailabilitySerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source='platform.name')

    class Meta:
        model = Availability
        fields = ('platform', 'url', 'is_available')


class YouTubeLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = YouTubeLink
        fields = ('title', 'url', 'is_official')


class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    cast = PersonSerializer(many=True, read_only=True)
    availabilities = AvailabilitySerializer(many=True, read_only=True)
    youtube_links = YouTubeLinkSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = (
            'id', 'tmdb_id', 'title', 'original_title', 'overview', 'release_date',
            'poster_path', 'vote_average', 'vote_count', 'popularity',
            'genres', 'cast', 'availabilities', 'youtube_links',
        )
