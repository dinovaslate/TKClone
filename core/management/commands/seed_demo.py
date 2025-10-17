from __future__ import annotations

import random
from datetime import date, datetime, timedelta, time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import Booking
from courts.models import Court, MaintenanceBlock

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate the database with demo courts, bookings, and maintenance blocks.'

    def handle(self, *args, **options):
        demo_user, _ = User.objects.get_or_create(
            username='demo', defaults={'email': 'demo@example.com'}
        )
        if not demo_user.has_usable_password():
            demo_user.set_password('demo12345')
            demo_user.save(update_fields=['password'])
        self.stdout.write(self.style.SUCCESS('Demo user ready (demo/demo12345).'))

        courts = self._seed_courts()
        self._seed_maintenance(courts)
        self._seed_bookings(demo_user, courts)
        self.stdout.write(self.style.SUCCESS('Demo data loaded.'))

    def _seed_courts(self):
        if Court.objects.exists():
            self.stdout.write('Courts already exist, skipping creation.')
            return list(Court.objects.all())

        payloads = [
            {
                'name': 'Arcadia Prime',
                'location': 'Central Jakarta',
                'description': 'Premium indoor court with climate control.',
                'surface_type': Court.SURFACE_SYNTHETIC,
                'length_m': 42,
                'width_m': 25,
                'price_per_hour': 250000,
                'open_time': time(6, 0),
                'close_time': time(23, 0),
                'image': 'https://images.unsplash.com/photo-1547955922-26be3c0c466a',
            },
            {
                'name': 'Greenfield Arena',
                'location': 'South Jakarta',
                'description': 'Outdoor field with natural grass and stadium lighting.',
                'surface_type': Court.SURFACE_NATURAL,
                'length_m': 45,
                'width_m': 27,
                'price_per_hour': 180000,
                'open_time': time(7, 0),
                'close_time': time(22, 0),
                'image': 'https://images.unsplash.com/photo-1509023464722-18d996393ca8',
            },
            {
                'name': 'Metro Sports Hub',
                'location': 'West Jakarta',
                'description': 'High-energy court with LED lighting and locker rooms.',
                'surface_type': Court.SURFACE_SYNTHETIC,
                'length_m': 40,
                'width_m': 24,
                'price_per_hour': 210000,
                'open_time': time(6, 0),
                'close_time': time(23, 0),
                'image': 'https://images.unsplash.com/photo-1508609349937-5ec4ae374ebf',
            },
            {
                'name': 'Riverside Pitch',
                'location': 'East Jakarta',
                'description': 'Community favorite with weekend tournaments.',
                'surface_type': Court.SURFACE_NATURAL,
                'length_m': 44,
                'width_m': 26,
                'price_per_hour': 160000,
                'open_time': time(7, 0),
                'close_time': time(21, 0),
                'image': 'https://images.unsplash.com/photo-1505685296765-3a2736de412f',
            },
            {
                'name': 'Skyline Court',
                'location': 'North Jakarta',
                'description': 'Rooftop futsal with panoramic skyline views.',
                'surface_type': Court.SURFACE_SYNTHETIC,
                'length_m': 38,
                'width_m': 22,
                'price_per_hour': 230000,
                'open_time': time(8, 0),
                'close_time': time(22, 0),
                'image': 'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b',
            },
            {
                'name': 'Legends Dome',
                'location': 'BSD City',
                'description': 'Tournament-ready dome with pro-grade turf.',
                'surface_type': Court.SURFACE_SYNTHETIC,
                'length_m': 46,
                'width_m': 28,
                'price_per_hour': 280000,
                'open_time': time(6, 0),
                'close_time': time(23, 0),
                'image': 'https://images.unsplash.com/photo-1530541930197-ff16ac917f23',
            },
        ]
        courts = [Court.objects.create(**payload) for payload in payloads]
        self.stdout.write(f'Created {len(courts)} courts.')
        return courts

    def _seed_maintenance(self, courts):
        MaintenanceBlock.objects.all().delete()
        today = date.today()
        tz = timezone.get_current_timezone()
        for court in courts[:3]:
            start = timezone.make_aware(datetime.combine(today + timedelta(days=3), time(12)), tz)
            MaintenanceBlock.objects.create(
                court=court,
                start_dt=start,
                end_dt=start + timedelta(hours=2),
                reason='Scheduled maintenance',
            )
        self.stdout.write('Maintenance windows scheduled.')

    def _seed_bookings(self, user, courts):
        Booking.objects.filter(user=user).delete()
        today = date.today()
        for court in courts:
            for offset in range(1, 6):
                start_hour = random.choice(range(court.open_time.hour, court.close_time.hour - 2))
                start = time(start_hour, 0)
                end = (datetime.combine(today, start) + timedelta(hours=2)).time()
                status = random.choice([Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED])
                booking = Booking(
                    user=user,
                    court=court,
                    date=today + timedelta(days=offset),
                    start_time=start,
                    end_time=end,
                    status=status,
                    payment_status=Booking.PAYMENT_PAID if status == Booking.STATUS_CONFIRMED else Booking.PAYMENT_UNPAID,
                )
                booking.full_clean()
                booking.save()
        self.stdout.write('Sample bookings created.')
