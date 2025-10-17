from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from courts.models import Court, MaintenanceBlock


class Booking(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_CANCELED = 'CANCELED'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELED, 'Canceled'),
    )

    PAYMENT_UNPAID = 'UNPAID'
    PAYMENT_PAID = 'PAID'
    PAYMENT_CHOICES = (
        (PAYMENT_UNPAID, 'Unpaid'),
        (PAYMENT_PAID, 'Paid'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bookings', on_delete=models.CASCADE)
    court = models.ForeignKey(Court, related_name='bookings', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default=PAYMENT_UNPAID)
    hold_expires_at = models.DateTimeField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=('court', 'date', 'start_time', 'end_time')),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.court.name} on {self.date}"

    @property
    def is_hold_active(self) -> bool:
        return self.status == self.STATUS_PENDING and self.hold_expires_at > timezone.now()

    @property
    def duration_hours(self) -> Decimal:
        start_dt = datetime.combine(self.date, self.start_time)
        end_dt = datetime.combine(self.date, self.end_time)
        hours = Decimal((end_dt - start_dt).total_seconds() / 3600)
        return hours

    def clean(self) -> None:
        if self.start_time >= self.end_time:
            raise ValidationError(['End time must be after start time.'])

        duration_minutes = (datetime.combine(self.date, self.end_time) - datetime.combine(self.date, self.start_time)).total_seconds() / 60
        if duration_minutes % 60 != 0:
            raise ValidationError(['Bookings must be in 60-minute blocks.'])

        if self.court.open_time > self.start_time or self.end_time > self.court.close_time:
            raise ValidationError(['Booking must be within the court operating hours.'])

        overlaps = Booking.objects.filter(
            court=self.court,
            date=self.date,
        ).exclude(pk=self.pk)
        overlaps = overlaps.filter(start_time__lt=self.end_time, end_time__gt=self.start_time)
        overlaps = overlaps.exclude(status=self.STATUS_CANCELED)
        overlaps = overlaps.exclude(status=self.STATUS_PENDING, hold_expires_at__lte=timezone.now())

        if overlaps.exists():
            raise ValidationError(['Selected slot is no longer available.'])

        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime.combine(self.date, self.start_time), tz)
        end_dt = timezone.make_aware(datetime.combine(self.date, self.end_time), tz)
        block_exists = MaintenanceBlock.objects.filter(
            court=self.court,
            start_dt__lt=end_dt,
            end_dt__gt=start_dt,
        ).exists()
        if block_exists:
            raise ValidationError(['Court is unavailable due to maintenance.'])

    def save(self, *args, **kwargs) -> None:
        if not self.hold_expires_at:
            self.hold_expires_at = timezone.now() + timedelta(minutes=10)
        self.total_price = (self.duration_hours * self.court.price_per_hour).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def confirm(self) -> None:
        self.status = self.STATUS_CONFIRMED
        self.payment_status = self.PAYMENT_PAID
        self.save(update_fields=['status', 'payment_status', 'updated_at'])

    def cancel(self) -> None:
        self.status = self.STATUS_CANCELED
        self.save(update_fields=['status', 'updated_at'])

    def restore(self) -> None:
        if self.status == self.STATUS_CANCELED:
            self.status = self.STATUS_PENDING
            self.payment_status = self.PAYMENT_UNPAID
            self.hold_expires_at = timezone.now() + timedelta(minutes=10)
            self.save(update_fields=['status', 'payment_status', 'hold_expires_at', 'updated_at'])
