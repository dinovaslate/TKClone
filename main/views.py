from __future__ import annotations

import calendar
import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import FilterForm, PaymentMethodForm, ReviewForm, SlotSelectionForm
from .models import Booking, BookingAddOn, Category, City, Review, TimeSlot, Venue, WishlistEntry


def show_login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("main:home")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = HttpResponseRedirect(reverse("main:home"))
        response.set_cookie("last_login", str(datetime.datetime.now()))
        return response

    return render(request, "main/login.html", {"form": form})


def show_register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("main:home")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat! Silakan login.")
        return redirect("main:login")

    return render(request, "main/register.html", {"form": form})


@login_required(login_url="/login/")
@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    response = HttpResponseRedirect(reverse("main:login"))
    response.delete_cookie("last_login")
    return response


def _apply_filters(queryset, form: FilterForm):
    if not form.is_valid():
        return queryset

    location = form.cleaned_data.get("location")
    category = form.cleaned_data.get("category")
    price = form.cleaned_data.get("price")

    if location:
        queryset = queryset.filter(city=location)
    if category:
        queryset = queryset.filter(category=category)
    if price is not None:
        queryset = queryset.filter(price_per_hour__lte=price)
    return queryset


@login_required(login_url="/login/")
def home(request: HttpRequest) -> HttpResponse:
    cities = City.objects.all()
    categories = Category.objects.all()
    filter_form = FilterForm(request.GET or None, cities=cities, categories=categories)

    base_queryset = Venue.objects.select_related("city", "category")
    filtered_venues = _apply_filters(base_queryset, filter_form).order_by("name")

    popular_venues = (
        base_queryset.annotate(
            popularity=models.Count(
                "bookings",
                filter=models.Q(bookings__status__in=Booking.ACTIVE_STATUSES),
            )
        )
        .order_by("-popularity", "name")[:3]
    )

    wishlisted_ids = set(request.user.wishlist_entries.values_list("venue_id", flat=True))

    context = {
        "filter_form": filter_form,
        "popular_venues": popular_venues,
        "venues": filtered_venues[:6],
        "wishlist_ids": wishlisted_ids,
        "active_page": "home",
    }
    return render(request, "main/home.html", context)


@login_required(login_url="/login/")
def catalog(request: HttpRequest) -> HttpResponse:
    cities = City.objects.all()
    categories = Category.objects.all()
    filter_form = FilterForm(request.GET or None, cities=cities, categories=categories)

    base_queryset = Venue.objects.select_related("city", "category")
    filtered_venues = _apply_filters(base_queryset, filter_form).order_by("name")

    wishlisted_ids = set(request.user.wishlist_entries.values_list("venue_id", flat=True))

    context = {
        "filter_form": filter_form,
        "venues": filtered_venues,
        "wishlist_ids": wishlisted_ids,
        "active_page": "catalog",
    }
    return render(request, "main/catalog.html", context)


@login_required(login_url="/login/")
def wishlist(request: HttpRequest) -> HttpResponse:
    entries = (
        WishlistEntry.objects.filter(user=request.user)
        .select_related("venue", "venue__city", "venue__category")
        .order_by("-created_at")
    )
    venues = [entry.venue for entry in entries]
    wishlist_ids = {venue.id for venue in venues}
    context = {
        "venues": venues,
        "wishlist_ids": wishlist_ids,
        "active_page": "wishlist",
    }
    return render(request, "main/wishlist.html", context)


@login_required(login_url="/login/")
def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    venue = get_object_or_404(Venue.objects.select_related("city", "category"), slug=slug)
    review_form = ReviewForm(request.POST or None)
    if request.method == "POST" and review_form.is_valid():
        Review.objects.create(
            user=request.user,
            venue=venue,
            rating=int(review_form.cleaned_data["rating"]),
            comment=review_form.cleaned_data["comment"],
        )
        messages.success(request, "Review berhasil ditambahkan!")
        return redirect("main:product_detail", slug=slug)

    today = timezone.localdate()
    month_start = today.replace(day=1)
    _, last_day = calendar.monthrange(month_start.year, month_start.month)
    calendar_days: list[dict[str, object]] = []
    first_available_date = None
    for day in range(1, last_day + 1):
        date_obj = month_start.replace(day=day)
        available_slots = venue.time_slots.filter(date=date_obj, is_booked=False)
        is_past = date_obj < today
        if available_slots.exists() and not is_past and first_available_date is None:
            first_available_date = date_obj
        calendar_days.append(
            {
                "date": date_obj,
                "has_slots": available_slots.exists(),
                "is_past": is_past,
                "url": reverse("main:booking_times", args=[venue.slug]) + f"?date={date_obj.isoformat()}",
            }
        )

    wishlisted = WishlistEntry.objects.filter(user=request.user, venue=venue).exists()
    reviews = venue.reviews.select_related("user")

    context = {
        "venue": venue,
        "review_form": review_form,
        "reviews": reviews,
        "calendar_days": calendar_days,
        "month_label": month_start.strftime("%B %Y"),
        "wishlisted": wishlisted,
        "first_available_date": first_available_date,
        "active_page": "catalog",
    }
    return render(request, "main/product_detail.html", context)


@login_required(login_url="/login/")
def booking_times(request: HttpRequest, slug: str) -> HttpResponse:
    venue = get_object_or_404(Venue.objects.select_related("city", "category"), slug=slug)
    date_str = request.GET.get("date") or request.POST.get("date")
    if not date_str:
        messages.error(request, "Tanggal tidak valid.")
        return redirect("main:product_detail", slug=slug)

    try:
        selected_date = datetime.date.fromisoformat(date_str)
    except ValueError:
        messages.error(request, "Tanggal tidak valid.")
        return redirect("main:product_detail", slug=slug)

    form = SlotSelectionForm(venue, selected_date, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        time_slot: TimeSlot = form.cleaned_data["time_slot"]
        addons = list(form.cleaned_data.get("addons"))
        if time_slot.is_booked or time_slot.is_past:
            messages.error(request, "Slot sudah dibooking, pilih slot lainnya.")
            return redirect(request.path + f"?date={selected_date.isoformat()}")

        duration = datetime.datetime.combine(selected_date, time_slot.end_time) - datetime.datetime.combine(
            selected_date, time_slot.start_time
        )
        hours = Decimal(duration.total_seconds()) / Decimal(3600)
        slot_price = (venue.price_per_hour * hours).quantize(Decimal("0.01"))
        addon_total = sum(addon.price for addon in addons)
        deposit = min(Decimal("10000.00"), slot_price + addon_total)
        total_amount = slot_price + addon_total

        booking = Booking.objects.create(
            user=request.user,
            venue=venue,
            time_slot=time_slot,
            deposit_amount=deposit,
            addon_total=addon_total,
            total_amount=total_amount,
        )

        BookingAddOn.objects.bulk_create([BookingAddOn(booking=booking, addon=addon) for addon in addons])

        time_slot.is_booked = True
        time_slot.save(update_fields=["is_booked"])

        return redirect("main:booking_payment", booking_id=booking.pk)

    available_slots = venue.time_slots.filter(date=selected_date, is_booked=False)
    if not available_slots.exists():
        messages.warning(request, "Tidak ada slot tersedia pada tanggal ini.")

    context = {
        "venue": venue,
        "form": form,
        "selected_date": selected_date,
        "active_page": "catalog",
    }
    return render(request, "main/booking_times.html", context)


@login_required(login_url="/login/")
def booking_payment(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = get_object_or_404(Booking.objects.select_related("venue", "time_slot"), pk=booking_id, user=request.user)

    form = PaymentMethodForm(request.POST or None, initial={"payment_method": booking.payment_method})

    if request.method == "POST":
        if "confirm" in request.POST and booking.status == Booking.STATUS_AWAITING_CONFIRMATION:
            booking.status = Booking.STATUS_CONFIRMED
            booking.save(update_fields=["status"])
            messages.success(request, "Pembayaran berhasil dikonfirmasi!")
            return redirect("main:booking_success", booking_id=booking.pk)

        if form.is_valid():
            method = form.cleaned_data["payment_method"]
            if not method:
                messages.error(request, "Pilih metode pembayaran terlebih dahulu.")
            else:
                booking.payment_method = method
                booking.status = Booking.STATUS_AWAITING_CONFIRMATION
                booking.save(update_fields=["payment_method", "status"])
                messages.info(request, "Menunggu konfirmasi pembayaran...")
            return redirect("main:booking_payment", booking_id=booking.pk)

    addons = booking.addons.all()

    context = {
        "booking": booking,
        "form": form,
        "addons": addons,
        "active_page": "catalog",
    }
    return render(request, "main/payment.html", context)


@login_required(login_url="/login/")
def booking_success(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = get_object_or_404(Booking.objects.select_related("venue"), pk=booking_id, user=request.user)
    if booking.status != Booking.STATUS_CONFIRMED:
        return redirect("main:booking_payment", booking_id=booking.pk)

    return render(
        request,
        "main/booking_success.html",
        {
            "booking": booking,
            "active_page": "catalog",
        },
    )


@login_required(login_url="/login/")
@require_POST
def toggle_wishlist(request: HttpRequest, slug: str) -> HttpResponse:
    venue = get_object_or_404(Venue, slug=slug)
    entry, created = WishlistEntry.objects.get_or_create(user=request.user, venue=venue)
    if not created:
        entry.delete()
        messages.info(request, f"{venue.name} dihapus dari wishlist.")
    else:
        messages.success(request, f"{venue.name} ditambahkan ke wishlist.")

    next_url = request.POST.get("next") or reverse("main:home")
    return redirect(next_url)


landing = home
