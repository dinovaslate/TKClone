from __future__ import annotations

from datetime import date
from typing import Iterable

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateformat import format as date_format
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from .forms import AddOnSelectionForm, LoginForm, RegisterForm, ReviewForm
from .models import Booking, Category, Review, Venue, VenueAvailability, WishlistItem


def _apply_filters(queryset: Iterable[Venue], request: HttpRequest):
    city = request.GET.get("city") or ""
    category_slug = request.GET.get("category") or ""
    max_price = request.GET.get("price") or ""

    if city:
        queryset = queryset.filter(city__iexact=city)
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)
    if max_price:
        try:
            max_price_value = int(max_price)
            queryset = queryset.filter(price_per_hour__lte=max_price_value)
        except ValueError:
            pass
    return queryset, {"city": city, "category": category_slug, "price": max_price}


def show_login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("main:home")

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        response = redirect("main:home")
        response.set_cookie("last_login", timezone.now().isoformat())
        return response

    return render(request, "main/auth_login.html", {"form": form})


def show_register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("main:home")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, "Registrasi berhasil! Silakan masuk dengan akun barumu.")
        return redirect("main:login")

    return render(request, "main/auth_register.html", {"form": form})


@login_required(login_url="main:login")
def logged_out(request: HttpRequest) -> HttpResponse:
    logout(request)
    response = redirect("main:login")
    response.delete_cookie("last_login")
    return response


@login_required(login_url="main:login")
def home(request: HttpRequest) -> HttpResponse:
    venues = Venue.objects.select_related("category").all()
    venues, selected = _apply_filters(venues, request)

    top_venues = (
        venues.order_by("-bookings_count", "name")[:3]
        if venues.exists()
        else Venue.objects.select_related("category").order_by("-bookings_count", "name")[:3]
    )

    wishlist_ids = set(
        WishlistItem.objects.filter(user=request.user).values_list("venue_id", flat=True)
    )

    context = {
        "top_venues": top_venues,
        "cities": Venue.objects.values_list("city", flat=True).distinct().order_by("city"),
        "categories": Category.objects.all(),
        "price_steps": [100000, 150000, 200000, 250000, 300000, 400000],
        "selected": selected,
        "wishlist_ids": wishlist_ids,
    }
    return render(request, "main/home.html", context)


@login_required(login_url="main:login")
def catalog(request: HttpRequest) -> HttpResponse:
    venues = Venue.objects.select_related("category").all()
    venues, selected = _apply_filters(venues, request)
    wishlist_ids = set(
        WishlistItem.objects.filter(user=request.user).values_list("venue_id", flat=True)
    )

    context = {
        "venues": venues,
        "cities": Venue.objects.values_list("city", flat=True).distinct().order_by("city"),
        "categories": Category.objects.all(),
        "price_steps": [100000, 150000, 200000, 250000, 300000, 400000],
        "selected": selected,
        "wishlist_ids": wishlist_ids,
    }
    return render(request, "main/catalog.html", context)


@login_required(login_url="main:login")
def wishlist(request: HttpRequest) -> HttpResponse:
    items = (
        WishlistItem.objects.filter(user=request.user)
        .select_related("venue", "venue__category")
        .order_by("-created_at")
    )
    context = {
        "items": items,
    }
    return render(request, "main/wishlist.html", context)


@login_required(login_url="main:login")
@require_POST
def toggle_wishlist(request: HttpRequest, slug: str) -> HttpResponse:
    venue = get_object_or_404(Venue, slug=slug)
    item, created = WishlistItem.objects.get_or_create(user=request.user, venue=venue)
    if not created:
        item.delete()
        messages.info(request, f"{venue.name} dihapus dari wishlist.")
    else:
        messages.success(request, f"{venue.name} ditambahkan ke wishlist.")

    referer = request.META.get("HTTP_REFERER") or reverse("main:catalog")
    return redirect(referer)


@login_required(login_url="main:login")
def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    venue = get_object_or_404(
        Venue.objects.select_related("category"), slug=slug
    )
    wishlist_ids = set(
        WishlistItem.objects.filter(user=request.user).values_list("venue_id", flat=True)
    )
    review_form = ReviewForm(request.POST or None)
    if request.method == "POST" and review_form.is_valid():
        Review.objects.create(
            venue=venue,
            user=request.user,
            rating=int(review_form.cleaned_data["rating"]),
            comment=review_form.cleaned_data["comment"],
        )
        messages.success(request, "Terima kasih atas reviewmu!")
        return redirect("main:product_detail", slug=slug)

    availability_dates = (
        venue.availabilities.filter(date__gte=date.today())
        .order_by("date")
        .values_list("date", flat=True)
        .distinct()
    )

    context = {
        "venue": venue,
        "wishlist_ids": wishlist_ids,
        "review_form": review_form,
        "reviews": venue.reviews.select_related("user"),
        "availability_dates": [
            {
                "value": d,
                "label": date_format(d, "j F Y"),
            }
            for d in availability_dates
        ],
    }
    return render(request, "main/detail.html", context)


@login_required(login_url="main:login")
def booking_schedule(request: HttpRequest, slug: str, date_str: str) -> HttpResponse:
    venue = get_object_or_404(Venue, slug=slug)
    selected_date = parse_date(date_str)
    if selected_date is None:
        raise Http404()
    slots = (
        venue.availabilities.filter(date=selected_date)
        .select_related("venue")
        .order_by("start_time")
    )
    if not slots:
        messages.warning(request, "Belum ada jadwal untuk tanggal tersebut.")

    context = {
        "venue": venue,
        "date": selected_date,
        "slots": slots,
    }
    return render(request, "main/schedule.html", context)


@login_required(login_url="main:login")
def book_slot(request: HttpRequest, slug: str, slot_id: int) -> HttpResponse:
    venue = get_object_or_404(Venue, slug=slug)
    slot = get_object_or_404(VenueAvailability, pk=slot_id, venue=venue)

    if slot.is_booked:
        messages.error(request, "Slot sudah direservasi orang lain.")
        return redirect("main:booking_schedule", slug=slug, date_str=slot.date.isoformat())

    form = AddOnSelectionForm(request.POST or None, venue=venue)
    if request.method == "POST" and form.is_valid():
        booking = Booking.objects.create(user=request.user, venue=venue, slot=slot)
        addons = list(form.cleaned_data["addons"])
        if addons:
            booking.addons.add(*addons)
        booking.sync_totals()
        booking.status = Booking.Status.PENDING
        booking.save()

        slot.is_booked = True
        slot.save(update_fields=["is_booked"])

        Venue.objects.filter(pk=venue.pk).update(bookings_count=F("bookings_count") + 1)
        venue.refresh_from_db(fields=["bookings_count"])

        messages.success(request, "Slot berhasil di-booking! Lanjut ke pembayaran.")
        return redirect("main:payment", booking_id=booking.pk)

    context = {
        "venue": venue,
        "slot": slot,
        "form": form,
    }
    return render(request, "main/book_slot.html", context)


@login_required(login_url="main:login")
def payment_page(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = get_object_or_404(
        Booking.objects.select_related("slot", "venue"), pk=booking_id, user=request.user
    )
    if booking.status == Booking.Status.CONFIRMED:
        return redirect("main:payment_success", booking_id=booking.pk)

    if request.method == "POST":
        method = request.POST.get("method")
        if method not in dict(Booking.PaymentMethod.choices):
            messages.error(request, "Metode pembayaran tidak dikenal.")
        else:
            booking.payment_method = method
            booking.status = Booking.Status.AWAITING_CONFIRMATION
            booking.save(update_fields=["payment_method", "status", "updated_at"])
            return redirect("main:payment_waiting", booking_id=booking.pk)

    context = {"booking": booking}
    return render(request, "main/payment.html", context)


@login_required(login_url="main:login")
def payment_waiting(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = get_object_or_404(
        Booking.objects.select_related("slot", "venue"), pk=booking_id, user=request.user
    )
    if booking.payment_method == "":
        return redirect("main:payment", booking_id=booking.pk)

    if request.method == "POST":
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["status", "updated_at"])
        messages.success(request, "Pembayaran terkonfirmasi. Selamat bermain!")
        return redirect("main:payment_success", booking_id=booking.pk)

    return render(request, "main/payment_waiting.html", {"booking": booking})


@login_required(login_url="main:login")
def payment_success(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = get_object_or_404(
        Booking.objects.select_related("slot", "venue"), pk=booking_id, user=request.user
    )
    if booking.status != Booking.Status.CONFIRMED:
        return redirect("main:payment", booking_id=booking.pk)

    return render(request, "main/payment_success.html", {"booking": booking})
