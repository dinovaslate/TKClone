from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - human readable representation
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Venue(TimestampedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="venues")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="venues")
    address = models.CharField(max_length=255)
    description = models.TextField()
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    cover_image = models.URLField()
    surface_type = models.CharField(max_length=100, blank=True)
    amenities = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name

    @property
    def bookings_count(self) -> int:
        return self.bookings.filter(status__in=Booking.ACTIVE_STATUSES).count()

    @property
    def average_rating(self) -> Decimal | None:
        aggregation = self.reviews.aggregate(models.Avg("rating"))
        rating: Decimal | None = aggregation["rating__avg"]
        if rating is None:
            return None
        return rating.quantize(Decimal("0.0"))


class VenuePhoto(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="photos")
    image_url = models.URLField()

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.venue.name} photo"


class WishlistEntry(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist_entries")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="wishlisted_by")

    class Meta:
        unique_together = ("user", "venue")
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.user} ❤️ {self.venue}"


class Review(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "venue", "comment", "created_at")

    def __str__(self) -> str:  # pragma: no cover
        return f"Review({self.user}, {self.venue})"


class AddOn(models.Model):
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    venues = models.ManyToManyField(Venue, related_name="addons", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class TimeSlot(TimestampedModel):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="time_slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("venue", "date", "start_time", "end_time")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.venue.name} {self.date} {self.start_time}-{self.end_time}"

    @property
    def is_past(self) -> bool:
        slot_datetime = timezone.make_aware(
            datetime.datetime.combine(self.date, self.end_time)
        )
        return slot_datetime < timezone.now()


class Booking(TimestampedModel):
    PAYMENT_QRIS = "qris"
    PAYMENT_GOPAY = "gopay"
    PAYMENT_PENDING = ""

    STATUS_RESERVED = "reserved"
    STATUS_AWAITING_CONFIRMATION = "awaiting_confirmation"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"

    PAYMENT_CHOICES = [
        (PAYMENT_PENDING, "Select payment"),
        (PAYMENT_QRIS, "QRIS"),
        (PAYMENT_GOPAY, "GoPay"),
    ]

    STATUS_CHOICES = [
        (STATUS_RESERVED, "Reserved"),
        (STATUS_AWAITING_CONFIRMATION, "Awaiting Confirmation"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    ACTIVE_STATUSES: Iterable[str] = (STATUS_RESERVED, STATUS_AWAITING_CONFIRMATION, STATUS_CONFIRMED)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="bookings")
    time_slot = models.OneToOneField(TimeSlot, on_delete=models.PROTECT, related_name="booking")
    addons = models.ManyToManyField(AddOn, through="BookingAddOn", related_name="bookings", blank=True)
    deposit_amount = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("10000.00"))
    addon_total = models.DecimalField(max_digits=9, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=12, choices=PAYMENT_CHOICES, default=PAYMENT_PENDING)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_RESERVED)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Booking #{self.pk} - {self.venue.name}"

    @property
    def balance_due(self) -> Decimal:
        return max(Decimal("0.00"), self.total_amount - self.deposit_amount)


class BookingAddOn(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    addon = models.ForeignKey(AddOn, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("booking", "addon")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.addon.name} x{self.quantity}"

    @property
    def subtotal(self) -> Decimal:
        return self.addon.price * self.quantity
