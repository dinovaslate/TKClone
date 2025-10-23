from __future__ import annotations

import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    BOOKING_TIME_SLOTS,
    BookingScheduleForm,
    PaymentMethodForm,
    RegistrationForm,
    ReviewForm,
    VenueFilterForm,
)
from .models import Booking, Category, Review, Venue, WishlistEntry


PRICE_RANGE_MAP = {
    "low": (Decimal("0"), Decimal("150000")),
    "mid": (Decimal("150000"), Decimal("300000")),
    "high": (Decimal("300000"), None),
}


def _apply_filters(venues, form):
    city = form.cleaned_data.get("city")
    category = form.cleaned_data.get("category")
    price_key = form.cleaned_data.get("price")

    if city:
        venues = venues.filter(city__iexact=city)
    if category:
        venues = venues.filter(category=category)
    if price_key:
        min_price, max_price = PRICE_RANGE_MAP.get(price_key, (None, None))
        if min_price is not None:
            venues = venues.filter(price_per_hour__gte=min_price)
        if max_price is not None:
            venues = venues.filter(price_per_hour__lte=max_price)
    return venues


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("main:home")

    form = AuthenticationForm(request, data=request.POST or None)
    for field in form.fields.values():
        field.widget.attrs.setdefault("placeholder", field.label)
        existing_class = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = (existing_class + " input-control").strip()
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, "Welcome back! Let’s find your next match.")
        return redirect("main:home")

    return render(request, "main/login.html", {"form": form})


def register_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("main:home")

    form = RegistrationForm(request.POST or None)
    for field in form.fields.values():
        field.widget.attrs.setdefault("placeholder", field.label)
        existing_class = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = (existing_class + " input-control").strip()
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created! Please sign in to continue.")
        return redirect("main:login")

    return render(request, "main/register.html", {"form": form})


@login_required(login_url="main:login")
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "You have been logged out. See you soon!")
    return redirect("main:login")


@login_required(login_url="main:login")
def home_view(request: HttpRequest) -> HttpResponse:
    venues = Venue.objects.select_related("category").all()
    categories = Category.objects.filter(venues__isnull=False).distinct()
    form = VenueFilterForm(
        data=request.GET or None,
        cities=venues.values_list("city", flat=True),
        categories=categories,
    )

    filtered_venues = venues
    if form.is_valid():
        filtered_venues = _apply_filters(filtered_venues, form)

    wishlist_ids = set(
        request.user.wishlist_entries.values_list("venue_id", flat=True)
    )

    popular_venues = (
        Venue.objects.select_related("category")
        .annotate(
            booking_count=Count(
                "bookings",
                filter=Q(bookings__status=Booking.Status.CONFIRMED),
            )
        )
        .order_by("-booking_count", "name")[:3]
    )

    context = {
        "filter_form": form,
        "venues": filtered_venues[:6],
        "popular_venues": popular_venues,
        "wishlist_ids": wishlist_ids,
    }
    return render(request, "main/home.html", context)


@login_required(login_url="main:login")
def catalog_view(request: HttpRequest) -> HttpResponse:
    venues = Venue.objects.select_related("category").all()
    categories = Category.objects.filter(venues__isnull=False).distinct()
    form = VenueFilterForm(
        data=request.GET or None,
        cities=venues.values_list("city", flat=True),
        categories=categories,
    )

    if form.is_valid():
        venues = _apply_filters(venues, form)

    wishlist_ids = set(
        request.user.wishlist_entries.values_list("venue_id", flat=True)
    )

    return render(
        request,
        "main/catalog.html",
        {
            "filter_form": form,
            "venues": venues,
            "wishlist_ids": wishlist_ids,
        },
    )


@login_required(login_url="main:login")
def wishlist_view(request: HttpRequest) -> HttpResponse:
    entries = (
        WishlistEntry.objects.filter(user=request.user)
        .select_related("venue", "venue__category")
        .order_by("-created_at")
    )
    venues = [entry.venue for entry in entries]
    wishlist_ids = {venue.id for venue in venues}
    return render(
        request,
        "main/wishlist.html",
        {"venues": venues, "wishlist_ids": wishlist_ids},
    )


@login_required(login_url="main:login")
@require_POST
def toggle_wishlist(request: HttpRequest, venue_id: int) -> HttpResponse:
    venue = get_object_or_404(Venue, pk=venue_id)
    entry, created = WishlistEntry.objects.get_or_create(user=request.user, venue=venue)
    if not created:
        entry.delete()
        messages.info(request, f"Removed {venue.name} from your wishlist.")
    else:
        messages.success(request, f"Added {venue.name} to your wishlist.")
    return redirect(request.POST.get("next") or "main:home")


@login_required(login_url="main:login")
def venue_detail(request: HttpRequest, slug: str) -> HttpResponse:
    venue = get_object_or_404(Venue.objects.select_related("category"), slug=slug)
    reviews = venue.reviews.select_related("user")
    in_wishlist = venue.id in request.user.wishlist_entries.values_list("venue_id", flat=True)
    review_form = ReviewForm(request.POST or None)

    if request.method == "POST" and review_form.is_valid():
        Review.objects.create(
            venue=venue,
            user=request.user,
            rating=review_form.cleaned_data["rating"],
            comment=review_form.cleaned_data["comment"],
        )
        messages.success(request, "Review posted! Thank you for sharing your experience.")
        return redirect("main:venue_detail", slug=venue.slug)

    today = timezone.localdate()
    available_dates = [today + datetime.timedelta(days=i) for i in range(0, 7)]

    return render(
        request,
        "main/detail.html",
        {
            "venue": venue,
            "reviews": reviews,
            "review_form": review_form,
            "available_dates": available_dates,
            "in_wishlist": in_wishlist,
            "time_slots": BOOKING_TIME_SLOTS,
        },
    )


@login_required(login_url="main:login")
def booking_schedule(request: HttpRequest, slug: str) -> HttpResponse:
    venue = get_object_or_404(Venue, slug=slug)
    date_str = request.GET.get("date") or request.POST.get("date")
    if not date_str:
        messages.error(request, "Please choose a date first.")
        return redirect("main:venue_detail", slug=venue.slug)

    try:
        selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid date selected.")
        return redirect("main:venue_detail", slug=venue.slug)

    form = BookingScheduleForm(request.POST or None, initial={"date": selected_date})
    selected_addons = request.POST.getlist("addons") if request.method == "POST" else []
    selected_time_slot = request.POST.get("time_slot") if request.method == "POST" else None

    if request.method == "POST" and form.is_valid():
        time_slot = form.cleaned_data["time_slot"]
        addons = list(form.cleaned_data["addons"])
        addon_total = sum((addon.price for addon in addons), Decimal("0"))
        base_price = venue.price_per_hour
        total_price = base_price + addon_total

        booking = Booking.objects.create(
            user=request.user,
            venue=venue,
            date=form.cleaned_data["date"],
            time_slot=time_slot,
            base_price=base_price,
            addon_total=addon_total,
            total_price=total_price,
        )
        booking.addons.set(addons)
        messages.success(request, "Time slot locked! Complete your payment to confirm the booking.")
        return redirect("main:payment", pk=booking.pk)

    return render(
        request,
        "main/booking_schedule.html",
        {
            "venue": venue,
            "selected_date": selected_date,
            "form": form,
            "selected_addons": selected_addons,
            "selected_time_slot": selected_time_slot,
        },
    )


@login_required(login_url="main:login")
def payment_view(request: HttpRequest, pk: int) -> HttpResponse:
    booking = get_object_or_404(Booking.objects.select_related("venue"), pk=pk, user=request.user)
    method_form = PaymentMethodForm(request.POST or None, initial={"payment_method": booking.payment_method})

    if request.method == "POST":
        if "confirm" in request.POST:
            if booking.status == Booking.Status.AWAITING_CONFIRMATION:
                booking.status = Booking.Status.CONFIRMED
                booking.confirmed_at = timezone.now()
                booking.save(update_fields=["status", "confirmed_at"])
                messages.success(request, "Booking confirmed! Enjoy your match.")
                return redirect("main:payment_success", pk=booking.pk)
            messages.warning(request, "Please choose a payment method first.")
        elif method_form.is_valid():
            booking.payment_method = method_form.cleaned_data["payment_method"]
            booking.status = Booking.Status.AWAITING_CONFIRMATION
            booking.save(update_fields=["payment_method", "status"])
            messages.info(request, "Waiting for your confirmation. Double-check the details below.")

    return render(
        request,
        "main/payment.html",
        {
            "booking": booking,
            "method_form": method_form,
        },
    )


@login_required(login_url="main:login")
def payment_success(request: HttpRequest, pk: int) -> HttpResponse:
    booking = get_object_or_404(Booking.objects.select_related("venue"), pk=pk, user=request.user)
    if booking.status != Booking.Status.CONFIRMED:
        return redirect("main:payment", pk=booking.pk)

    return render(request, "main/payment_success.html", {"booking": booking})
