from django.contrib import admin
from .models import Industry, Genre, Person, Platform, Movie, Availability, YouTubeLink, Rating

@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')
    search_fields = ('name',)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'industry', 'release_date', 'popularity')
    list_filter = ('industry','genres')
    search_fields = ('title', 'original_title', 'synopsis')
    filter_horizontal = ('genres', 'cast')

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('movie', 'platform', 'is_available')
    list_filter = ('platform', 'is_available')
    search_fields = ('movie__title', 'platform__name')

@admin.register(YouTubeLink)
class YouTubeLinkAdmin(admin.ModelAdmin):
    list_display = ('movie', 'title', 'is_official', 'added_at')
    search_fields = ('movie__title', 'title')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('movie', 'user', 'score', 'created_at')
    search_fields = ('movie__title', 'user__username')
    list_filter = ('score',)
