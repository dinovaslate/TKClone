from __future__ import annotations

from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils.text import slugify


def seed_initial_data(apps, schema_editor):
    Category = apps.get_model("main", "Category")
    Venue = apps.get_model("main", "Venue")
    AddOn = apps.get_model("main", "AddOn")
    Booking = apps.get_model("main", "Booking")
    User = apps.get_model("auth", "User")

    def get_category(name: str):
        slug = slugify(name)
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={"slug": slug},
        )
        if not category.slug:
            category.slug = slug
            category.save(update_fields=["slug"])
        return category

    categories = {
        "Futsal": get_category("Futsal"),
        "Mini Soccer": get_category("Mini Soccer"),
        "Voli": get_category("Voli"),
        "Basket": get_category("Basket"),
    }

    venues_data = [
        {
            "name": "Mandala Futsal Dome",
            "city": "Jakarta",
            "address": "Jl. Mandala Raya No. 8, Jakarta Selatan",
            "category": categories["Futsal"],
            "price_per_hour": Decimal("250000"),
            "description": "Lapangan futsal indoor premium dengan rumput sintetis generasi terbaru dan fasilitas ruang ganti modern.",
            "image_url": "https://images.unsplash.com/photo-1544991181-7c1e2b3cef32",
            "hero_image_url": "https://images.unsplash.com/photo-1522778526097-ce0a22ceb253",
        },
        {
            "name": "Jogja Soccer Park",
            "city": "Yogyakarta",
            "address": "Jl. Kaliurang KM 5, Sleman",
            "category": categories["Mini Soccer"],
            "price_per_hour": Decimal("320000"),
            "description": "Arena mini soccer outdoor dengan pemandangan gunung Merapi dan tribun penonton yang nyaman.",
            "image_url": "https://images.unsplash.com/photo-1471295253337-3ceaaedca402",
            "hero_image_url": "https://images.unsplash.com/photo-1518091043644-c1d4457512c6",
        },
        {
            "name": "Surabaya Volley Center",
            "city": "Surabaya",
            "address": "Kompleks Olahraga Dharmahusada",
            "category": categories["Voli"],
            "price_per_hour": Decimal("180000"),
            "description": "Lapangan voli indoor berstandar turnamen dengan pencahayaan profesional dan seating area.",
            "image_url": "https://images.unsplash.com/photo-1517649763962-0c623066013b",
            "hero_image_url": "https://images.unsplash.com/photo-1505664194779-8beaceb93744",
        },
        {
            "name": "Bandung Hoop Arena",
            "city": "Bandung",
            "address": "Jl. Setiabudi No. 45",
            "category": categories["Basket"],
            "price_per_hour": Decimal("275000"),
            "description": "Court basket indoor dengan lantai kayu solid, papan skor digital, dan ruang istirahat tim.",
            "image_url": "https://images.unsplash.com/photo-1505666284453-01c01241da43",
            "hero_image_url": "https://images.unsplash.com/photo-1509228468518-180dd4864904",
        },
        {
            "name": "Bali Seaside Pitch",
            "city": "Denpasar",
            "address": "Pantai Mertasari, Sanur",
            "category": categories["Mini Soccer"],
            "price_per_hour": Decimal("360000"),
            "description": "Pengalaman bermain bola di tepi pantai dengan fasilitas shower dan lounge santai.",
            "image_url": "https://images.unsplash.com/photo-1489515217757-5fd1be406fef",
            "hero_image_url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211",
        },
    ]

    created_venues = []
    for data in venues_data:
        defaults = data | {"slug": slugify(data["name"])}
        venue, created = Venue.objects.get_or_create(
            name=data["name"],
            defaults=defaults,
        )
        if created is False:
            updated = False
            if not venue.slug:
                venue.slug = slugify(venue.name)
                updated = True
            for field, value in data.items():
                if getattr(venue, field) != value:
                    setattr(venue, field, value)
                    updated = True
            if updated:
                venue.save()
        created_venues.append(venue)

    addons = [
        {
            "name": "Professional Coach",
            "description": "Pendampingan taktik dan strategi selama sesi bermain.",
            "price": Decimal("150000"),
        },
        {
            "name": "Match Highlights Video",
            "description": "Rekaman video HD dengan highlights otomatis.",
            "price": Decimal("95000"),
        },
        {
            "name": "Hydration Package",
            "description": "Mineral water dan isotonic drink untuk 10 orang.",
            "price": Decimal("45000"),
        },
        {
            "name": "Premium Ball Rental",
            "description": "2 bola official match quality.",
            "price": Decimal("30000"),
        },
    ]

    for addon in addons:
        AddOn.objects.get_or_create(name=addon["name"], defaults=addon)

    demo_user, _ = User.objects.get_or_create(
        username="arenarent_demo",
        defaults={"password": make_password("playarena123"), "email": "demo@arenarent.test"},
    )

    for idx, venue in enumerate(created_venues):
        for _ in range(idx + 1):
            Booking.objects.create(
                user=demo_user,
                venue=venue,
                date="2025-01-0{}".format((idx % 5) + 1),
                time_slot="18:00-20:00",
                base_price=venue.price_per_hour,
                addon_total=Decimal("0"),
                total_price=venue.price_per_hour,
                status="confirmed",
            )


def remove_initial_data(apps, schema_editor):
    Venue = apps.get_model("main", "Venue")
    AddOn = apps.get_model("main", "AddOn")
    Category = apps.get_model("main", "Category")
    Booking = apps.get_model("main", "Booking")
    User = apps.get_model("auth", "User")

    Booking.objects.filter(user__username="arenarent_demo").delete()
    User.objects.filter(username="arenarent_demo").delete()

    venue_names = [
        "Mandala Futsal Dome",
        "Jogja Soccer Park",
        "Surabaya Volley Center",
        "Bandung Hoop Arena",
        "Bali Seaside Pitch",
    ]
    Venue.objects.filter(name__in=venue_names).delete()

    addon_names = [
        "Professional Coach",
        "Match Highlights Video",
        "Hydration Package",
        "Premium Ball Rental",
    ]
    AddOn.objects.filter(name__in=addon_names).delete()

    Category.objects.filter(name__in=["Futsal", "Mini Soccer", "Voli", "Basket"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_initial_data, remove_initial_data),
    ]
