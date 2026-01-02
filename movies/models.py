from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Industry(models.Model):
    """Bollywood, Hollywood, Tollywood, etc."""
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Person(models.Model):
    """Actor / Actress (hero, heroine, supporting)."""
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Platform(models.Model):
    """OTT platform (Netflix, Prime, Hotstar...)."""
    name = models.CharField(max_length=120, unique=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    tmdb_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    title = models.CharField(max_length=300)
    original_title = models.CharField(max_length=300, blank=True, null=True)
    synopsis = models.TextField(blank=True, null=True)
    overview = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    runtime_minutes = models.PositiveIntegerField(blank=True, null=True)
    poster_path = models.CharField(max_length=300, blank=True, null=True)

    # ranking / popularity
    popularity = models.FloatField(default=0.0)
    vote_average = models.FloatField(null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True)

    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    genres = models.ManyToManyField(Genre, blank=True, related_name='movies')
    cast = models.ManyToManyField(Person, blank=True, related_name='movies')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-popularity', '-vote_average', '-release_date']

    def __str__(self):
        return self.title


class Availability(models.Model):
    """Which platform a movie is available on and the link to it."""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='availabilities')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    url = models.URLField(blank=True, null=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('movie', 'platform')

    def __str__(self):
        return f"{self.movie} on {self.platform}"


class YouTubeLink(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='youtube_links')
    url = models.URLField()
    title = models.CharField(max_length=300, blank=True, null=True)
    is_official = models.BooleanField(default=False)  # mark if official/legal
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"YouTube: {self.movie} ({'official' if self.is_official else 'link'})"


class Rating(models.Model):
    """User rating for a movie."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    score = models.FloatField()  # 1.0 - 5.0
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.score} — {self.movie} ({self.user})"

class Availability(models.Model):
    """Which platform a movie is available on and the link to it."""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='availabilities')
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    url = models.URLField(blank=True, null=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('movie', 'platform')

    def __str__(self):
        return f"{self.movie} on {self.platform}"

class YouTubeLink(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='youtube_links')
    url = models.URLField()
    title = models.CharField(max_length=300, blank=True, null=True)
    is_official = models.BooleanField(default=False)  # mark if official/legal
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"YouTube: {self.movie} ({'official' if self.is_official else 'link'})"

class Rating(models.Model):
    """User rating for a movie. If user is null, it can be an anonymous/system rating."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    score = models.FloatField()  # 1.0 - 5.0 (you can enforce ranges in serializers or forms)
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.score} — {self.movie} ({self.user})"

