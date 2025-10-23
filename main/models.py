from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify

User = get_user_model()


class Category(models.Model):
    """High level grouping for a venue (football, futsal, etc)."""

    name = models.CharField(max_length=75, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - human readable output only
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Venue(models.Model):
    """A rentable sport venue."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    hero_image_url = models.URLField(blank=True)
    card_image_url = models.URLField(blank=True)
    surface = models.CharField(max_length=120, blank=True)
    size = models.CharField(max_length=120, blank=True)
    price_per_hour = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, related_name="venues", on_delete=models.CASCADE)
    bookings_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - human readable output only
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def average_rating(self) -> float:
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(review.rating for review in reviews if review.rating) / len(reviews), 1)


class VenueAvailability(models.Model):
    """Concrete time slot for a venue."""

    venue = models.ForeignKey(Venue, related_name="availabilities", on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("venue", "date", "start_time", "end_time")

    def __str__(self) -> str:  # pragma: no cover - human readable output only
        return f"{self.venue.name} - {self.date} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    @property
    def duration_hours(self) -> float:
        delta = (self.end_time.hour + self.end_time.minute / 60) - (
            self.start_time.hour + self.start_time.minute / 60
        )
        return max(delta, 0)

    @property
    def estimated_price(self) -> int:
        return int(self.duration_hours * self.venue.price_per_hour)


class AddOn(models.Model):
    """Additional optional services that can be booked along a slot."""

    venue = models.ForeignKey(Venue, related_name="addons", on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    price = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["venue", "price"]

    def __str__(self) -> str:  # pragma: no cover - human readable output only
        return f"{self.name} ({self.venue.name})"


class WishlistItem(models.Model):
    user = models.ForeignKey(User, related_name="wishlist_items", on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, related_name="wishlisted_by", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "venue")

    def __str__(self) -> str:  # pragma: no cover - human readable output only
        return f"{self.user} ➝ {self.venue}"


class Review(models.Model):
    venue = models.ForeignKey(Venue, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="reviews", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - human readable output only
        return f"{self.venue} review by {self.user}"


class Booking(models.Model):
    class PaymentMethod(models.TextChoices):
        QRIS = "qris", "QRIS"
        GOPAY = "gopay", "GoPay"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        AWAITING_CONFIRMATION = "awaiting_confirmation", "Awaiting confirmation"
        CONFIRMED = "confirmed", "Confirmed"

    user = models.ForeignKey(User, related_name="bookings", on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, related_name="bookings", on_delete=models.CASCADE)
    slot = models.OneToOneField(VenueAvailability, related_name="booking", on_delete=models.CASCADE)
    total_price = models.PositiveIntegerField(default=0)
    deposit_amount = models.PositiveIntegerField(default=10000)
    addons = models.ManyToManyField("AddOn", through="BookingAddon", related_name="bookings", blank=True)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover - human readable output only
        return f"Booking #{self.pk} by {self.user}"

    def sync_totals(self):
        addons_total = sum(addon.price for addon in self.addons.all())
        slot_cost = self.slot.estimated_price
        self.total_price = slot_cost + addons_total
        self.deposit_amount = min(10000, self.total_price)
        if addons_total:
            self.deposit_amount = 10000


class BookingAddon(models.Model):
    booking = models.ForeignKey(Booking, related_name="booking_addons", on_delete=models.CASCADE)
    addon = models.ForeignKey(AddOn, related_name="addon_bookings", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("booking", "addon")

    def __str__(self) -> str:  # pragma: no cover - human readable output only
        return f"{self.booking} + {self.addon}"

