from datetime import date

from django.shortcuts import render

from courts.models import Court


def home(request):
    featured_courts = Court.objects.filter(is_active=True).order_by('price_per_hour')[:6]
    context = {
        "featured_courts": featured_courts,
        "search_defaults": {
            "date": date.today().isoformat(),
        },
    }
    return render(request, "core/home.html", context)
