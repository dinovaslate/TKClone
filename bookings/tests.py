from datetime import date, datetime, timedelta, time

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from courts.models import Court, MaintenanceBlock


User = get_user_model()


class BookingRulesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='secret123')
        self.client = Client()
        self.client.force_login(self.user)
        self.court = Court.objects.create(
            name='Arcadia Prime',
            location='Jakarta',
            description='Indoor futsal court with premium turf.',
            surface_type=Court.SURFACE_SYNTHETIC,
            length_m=42,
            width_m=25,
            price_per_hour=250000,
            open_time=time(hour=6),
            close_time=time(hour=23),
            image='https://example.com/court.jpg',
        )

    def _create_booking(self, **kwargs):
        booking = Booking(**kwargs)
        booking.full_clean()
        booking.save()
        return booking

    def test_overlap_prevention(self):
        booking_date = date.today() + timedelta(days=1)
        self._create_booking(
            user=self.user,
            court=self.court,
            date=booking_date,
            start_time=time(hour=10),
            end_time=time(hour=11),
            status=Booking.STATUS_CONFIRMED,
        )

        with self.assertRaisesMessage(ValidationError, 'Selected slot is no longer available.'):
            self._create_booking(
                user=self.user,
                court=self.court,
                date=booking_date,
                start_time=time(hour=10),
                end_time=time(hour=12),
            )

    def test_hold_expiry_frees_slot(self):
        booking_date = date.today() + timedelta(days=1)
        existing = self._create_booking(
            user=self.user,
            court=self.court,
            date=booking_date,
            start_time=time(hour=9),
            end_time=time(hour=10),
        )
        existing.hold_expires_at = timezone.now() - timedelta(minutes=1)
        existing.save(update_fields=['hold_expires_at'])

        new_booking = self._create_booking(
            user=self.user,
            court=self.court,
            date=booking_date,
            start_time=time(hour=9),
            end_time=time(hour=10),
        )
        self.assertTrue(new_booking.pk)

    def test_price_calculation(self):
        booking_date = date.today() + timedelta(days=1)
        booking = self._create_booking(
            user=self.user,
            court=self.court,
            date=booking_date,
            start_time=time(hour=8),
            end_time=time(hour=10),
        )
        self.assertEqual(float(booking.total_price), 500000.0)

    def test_availability_endpoint_marks_states(self):
        booking_date = date.today() + timedelta(days=1)
        self._create_booking(
            user=self.user,
            court=self.court,
            date=booking_date,
            start_time=time(hour=7),
            end_time=time(hour=8),
            status=Booking.STATUS_CONFIRMED,
        )
        tz = timezone.get_current_timezone()
        MaintenanceBlock.objects.create(
            court=self.court,
            start_dt=timezone.make_aware(datetime.combine(booking_date, time(hour=12)), tz),
            end_dt=timezone.make_aware(datetime.combine(booking_date, time(hour=14)), tz),
            reason='Turf grooming',
        )

        response = self.client.get(reverse('core:api-availability'), {'court_id': self.court.id, 'date': booking_date.isoformat()})
        self.assertEqual(response.status_code, 200)
        data = response.json()['data']['slots']
        booked_slot = next(slot for slot in data if slot['start_time'] == '07:00')
        blocked_slot = next(slot for slot in data if slot['start_time'] == '12:00')
        self.assertEqual(booked_slot['status'], 'booked')
        self.assertEqual(blocked_slot['status'], 'blocked')
