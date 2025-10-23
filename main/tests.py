from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Category, Review, Venue, WishlistEntry


class ArenaRentFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "testpass123"
        self.user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password=self.password,
        )
        self.venue = Venue.objects.first()
        if not self.venue:
            category = Category.objects.create(name="Test", slug="test")
            self.venue = Venue.objects.create(
                name="Test Venue",
                slug="test-venue",
                city="Jakarta",
                category=category,
                price_per_hour=100000,
                description="Test description",
                image_url="https://example.com/test.jpg",
            )

    def test_login_required_redirects(self):
        response = self.client.get(reverse("main:home"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("main:login")))

    def test_catalog_filter_by_city(self):
        self.client.login(username=self.user.username, password=self.password)
        city = self.venue.city
        response = self.client.get(reverse("main:catalog"), {"city": city})
        self.assertEqual(response.status_code, 200)
        venues = response.context["venues"]
        self.assertTrue(all(v.city.lower() == city.lower() for v in venues))

    def test_toggle_wishlist_creates_entry(self):
        self.client.login(username=self.user.username, password=self.password)
        toggle_url = reverse("main:toggle_wishlist", args=[self.venue.id])
        response = self.client.post(toggle_url, {"next": reverse("main:home")})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            WishlistEntry.objects.filter(user=self.user, venue=self.venue).exists()
        )

    def test_post_review(self):
        self.client.login(username=self.user.username, password=self.password)
        detail_url = reverse("main:venue_detail", args=[self.venue.slug])
        payload = {"rating": 5, "comment": "Fantastic pitch!"}
        response = self.client.post(detail_url, payload, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Review.objects.filter(user=self.user, venue=self.venue, comment__icontains="fantastic").exists()
        )
