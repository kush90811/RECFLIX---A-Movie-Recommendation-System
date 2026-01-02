from django.test import TestCase
from django.urls import reverse
from .models import Movie, Genre, Person, Platform, Availability, YouTubeLink

class MovieAPITest(TestCase):
    def setUp(self):
        g = Genre.objects.create(name='Comedy')
        p = Person.objects.create(name='Test Actor')
        platform = Platform.objects.create(name='Netflix')

        m1 = Movie.objects.create(tmdb_id='1001', title='Funny One', overview='A comedy', popularity=10.0, vote_average=7.5)
        m1.genres.add(g)
        m1.cast.add(p)
        Availability.objects.create(movie=m1, platform=platform, url='https://netflix.example/1001')
        YouTubeLink.objects.create(movie=m1, url='https://youtube.example/watch?v=abc', title='Trailer', is_official=True)

        m2 = Movie.objects.create(tmdb_id='1002', title='Serious One', overview='A drama', popularity=5.0, vote_average=8.0)
        # m2 not in Comedy

    def test_list_movies(self):
        url = reverse('api-movies-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(isinstance(data, list))
        self.assertTrue(any(m['title']=='Funny One' for m in data))

    def test_filter_by_genre(self):
        url = reverse('api-movies-list') + '?genre=Comedy'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Funny One')

    def test_movie_detail(self):
        m = Movie.objects.get(tmdb_id='1001')
        url = reverse('api-movie-detail', args=[m.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('youtube_links', data)
        self.assertIn('availabilities', data)

    def test_best_in_genre(self):
        url = reverse('api-best-in-genre') + '?genre=Comedy'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['title'], 'Funny One')

    def test_recommend(self):
        url = reverse('api-recommend') + '?genres=Comedy&actors=Test+Actor'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(isinstance(data, list))
        self.assertTrue(any(m['title']=='Funny One' for m in data))
