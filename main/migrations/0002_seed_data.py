from __future__ import annotations

import datetime
from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils.text import slugify

VENUES = [
    {
        "name": "Jakarta Star Arena",
        "city": "Jakarta",
        "address": "Jl. Gatot Subroto No. 12, Jakarta",
        "category": "Football",
        "price": 350000,
        "surface": "Rumput sintetis FIFA Quality",
        "size": "105m x 68m",
        "hero": "https://images.unsplash.com/photo-1471295253337-3ceaaedca402?auto=format&fit=crop&w=1400&q=80",
        "card": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=900&q=80",
        "bookings": 82,
        "description": "Stadion mini berstandar profesional dengan pencahayaan kelas broadcast dan ruang ganti modern.",
        "addons": [
            ("Official Referee", 75000, "Wasit berlisensi untuk menjaga jalannya pertandingan"),
            ("Broadcast Camera", 120000, "Live streaming 2 kamera lengkap dengan operator"),
        ],
    },
    {
        "name": "Bandung Velocity Dome",
        "city": "Bandung",
        "address": "Jl. Setiabudi No. 88, Bandung",
        "category": "Futsal",
        "price": 220000,
        "surface": "Vinyl shock-absorbing",
        "size": "42m x 25m",
        "hero": "https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=1400&q=80",
        "card": "https://images.unsplash.com/photo-1471295253337-3ceaaedca402?auto=format&fit=crop&w=900&q=80",
        "bookings": 64,
        "description": "Arena futsal indoor dengan sistem pendingin udara dan scoreboard digital.",
        "addons": [
            ("Match Photographer", 65000, "Dokumentasi 30 foto aksi terbaik"),
            ("Tactical Whiteboard", 25000, "Whiteboard magnetik untuk briefing tim"),
        ],
    },
    {
        "name": "Surabaya Coastal Pitch",
        "city": "Surabaya",
        "address": "Jl. Kenjeran Raya No. 45, Surabaya",
        "category": "Football",
        "price": 280000,
        "surface": "Hybrid grass",
        "size": "100m x 64m",
        "hero": "https://images.unsplash.com/photo-1508609349937-5ec4ae374ebf?auto=format&fit=crop&w=1400&q=80",
        "card": "https://images.unsplash.com/photo-1519821172141-b5d8f7fcde5c?auto=format&fit=crop&w=900&q=80",
        "bookings": 58,
        "description": "Lapangan outdoor dengan panorama pantai dan fasilitas shower air hangat.",
        "addons": [
            ("Ice Bath Setup", 55000, "Perlengkapan recovery portable"),
            ("Match Balls x3", 30000, "Bola premium Nike Flight"),
        ],
    },
    {
        "name": "Jogja Heritage Court",
        "city": "Yogyakarta",
        "address": "Jl. Kaliurang KM 6, Yogyakarta",
        "category": "Basketball",
        "price": 200000,
        "surface": "Maple hardwood",
        "size": "28m x 15m",
        "hero": "https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=1400&q=80",
        "card": "https://images.unsplash.com/photo-1519052537078-e6302a4968d4?auto=format&fit=crop&w=900&q=80",
        "bookings": 71,
        "description": "Court basket indoor bernuansa heritage dengan seating area untuk 200 penonton.",
        "addons": [
            ("Scoreboard Operator", 45000, "Petugas pengelola scoreboard dan buzzer"),
            ("Sports Therapist", 90000, "Therapist on-call selama sesi"),
        ],
    },
    {
        "name": "Bali Sunset Arena",
        "city": "Bali",
        "address": "Jl. Sunset Road No. 19, Badung",
        "category": "Football",
        "price": 320000,
        "surface": "Natural grass",
        "size": "102m x 66m",
        "hero": "https://images.unsplash.com/photo-1505842465776-3acb7acf5afc?auto=format&fit=crop&w=1400&q=80",
        "card": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?auto=format&fit=crop&w=900&q=80",
        "bookings": 54,
        "description": "Lapangan tropis dengan lampu LED dan lounge pasca-pertandingan.",
        "addons": [
            ("DJ Booth", 80000, "Suasana musik untuk turnamen spesial"),
            ("Cooling Towels", 35000, "20 handuk dingin siap pakai"),
        ],
    },
]

REVIEWS = [
    ("Jakarta Star Arena", "Arena terawat dan lighting sangat terang.", 5),
    ("Bandung Velocity Dome", "AC dingin, cocok untuk turnamen malam.", 4),
    ("Jogja Heritage Court", "Lantai kayu empuk dan nyaman untuk pivot.", 5),
]


def seed_data(apps, schema_editor):
    Category = apps.get_model("main", "Category")
    Venue = apps.get_model("main", "Venue")
    AddOn = apps.get_model("main", "AddOn")
    VenueAvailability = apps.get_model("main", "VenueAvailability")
    Review = apps.get_model("main", "Review")
    User = apps.get_model("auth", "User")

    user, created = User.objects.get_or_create(
        username="ragaspace",
        defaults={
            "email": "hello@ragaspace.test",
            "password": make_password("ragaspace123"),
        },
    )

    categories = {}
    for venue_data in VENUES:
        cat_name = venue_data["category"]
        category, created = Category.objects.get_or_create(
            name=cat_name,
            defaults={"slug": slugify(cat_name)},
        )
        if created is False and not category.slug:
            category.slug = slugify(cat_name)
            category.save(update_fields=["slug"])
        categories[cat_name] = category

    today = datetime.date.today()
    for venue_data in VENUES:
        category = categories[venue_data["category"]]
        venue = Venue.objects.create(
            name=venue_data["name"],
            city=venue_data["city"],
            address=venue_data["address"],
            description=venue_data["description"],
            hero_image_url=venue_data["hero"],
            card_image_url=venue_data["card"],
            surface=venue_data["surface"],
            size=venue_data["size"],
            price_per_hour=venue_data["price"],
            category=category,
            bookings_count=venue_data["bookings"],
            slug=slugify(venue_data["name"]),
        )
        for name, price, description in venue_data["addons"]:
            AddOn.objects.create(venue=venue, name=name, price=price, description=description)

        for offset in range(3):
            target_date = today + datetime.timedelta(days=offset * 2 + 1)
            VenueAvailability.objects.get_or_create(
                venue=venue,
                date=target_date,
                start_time=datetime.time(hour=17),
                end_time=datetime.time(hour=19),
            )
            VenueAvailability.objects.get_or_create(
                venue=venue,
                date=target_date,
                start_time=datetime.time(hour=19, minute=30),
                end_time=datetime.time(hour=21, minute=30),
            )

    first_user = user
    if first_user:
        for venue_name, comment, rating in REVIEWS:
            venue = Venue.objects.filter(name=venue_name).first()
            if venue:
                Review.objects.create(venue=venue, user=first_user, comment=comment, rating=rating)


def remove_data(apps, schema_editor):
    Venue = apps.get_model("main", "Venue")
    Category = apps.get_model("main", "Category")
    Venue.objects.all().delete()
    Category.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, remove_data),
    ]
