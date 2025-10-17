from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from bookings.models import Booking

from .models import Court, FavoriteCourt, MaintenanceBlock


def court_list(request):
    return render(request, 'courts/list.html')


def court_detail(request, pk: int):
    court = get_object_or_404(Court, pk=pk, is_active=True)
    today = date.today()
    days = [today + timedelta(days=offset) for offset in range(7)]
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = FavoriteCourt.objects.filter(user=request.user, court=court).exists()
    context = {
        'court': court,
        'days': days,
        'is_favorite': is_favorite,
    }
    return render(request, 'courts/detail.html', context)


def _filter_courts(request):
    queryset = Court.objects.filter(is_active=True)
    query = request.GET.get('query')
    if query:
        queryset = queryset.filter(models.Q(name__icontains=query) | models.Q(location__icontains=query))
    surface = request.GET.get('surface')
    if surface:
        queryset = queryset.filter(surface_type=surface)
    min_price = request.GET.get('min_price')
    if min_price:
        queryset = queryset.filter(price_per_hour__gte=min_price)
    max_price = request.GET.get('max_price')
    if max_price:
        queryset = queryset.filter(price_per_hour__lte=max_price)
    return queryset.order_by('price_per_hour')


@require_GET
def api_courts(request):
    queryset = _filter_courts(request)
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)
    results = [
        {
            'id': court.id,
            'name': court.name,
            'location': court.location,
            'price_per_hour': float(court.price_per_hour),
            'surface_type': court.get_surface_type_display(),
            'image': court.image,
        }
        for court in page.object_list
    ]
    return JsonResponse({'success': True, 'data': {'results': results, 'page': page.number, 'pages': paginator.num_pages}})


def _slot_range(court: Court, booking_date: date):
    start_dt = datetime.combine(booking_date, court.open_time)
    end_dt = datetime.combine(booking_date, court.close_time)
    current = start_dt
    while current < end_dt:
        yield current
        current += timedelta(hours=1)


def _build_slot_payload(court: Court, slot_start: datetime, now: datetime):
    slot_end = slot_start + timedelta(hours=1)
    tz = timezone.get_current_timezone()
    slot_start_aware = timezone.make_aware(slot_start, tz)
    slot_end_aware = timezone.make_aware(slot_end, tz)
    label = f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
    bookings_qs = Booking.objects.filter(
        court=court,
        date=slot_start.date(),
        start_time__lt=slot_end.time(),
        end_time__gt=slot_start.time(),
    ).exclude(status=Booking.STATUS_CANCELED)
    bookings_qs = bookings_qs.exclude(status=Booking.STATUS_PENDING, hold_expires_at__lte=now)
    is_booked = bookings_qs.exists()

    block_exists = MaintenanceBlock.objects.filter(
        court=court,
        start_dt__lt=slot_end_aware,
        end_dt__gt=slot_start_aware,
    ).exists()

    if block_exists:
        status = 'blocked'
    elif is_booked:
        status = 'booked'
    else:
        status = 'available'

    disabled = slot_end_aware <= now or status != 'available'

    return {
        'start_time': slot_start.strftime('%H:%M'),
        'end_time': slot_end.strftime('%H:%M'),
        'label': label,
        'status': status,
        'disabled': disabled,
        'price': float(court.price_per_hour),
        'displayDate': slot_start.strftime('%d %b %Y'),
    }


@require_GET
def api_availability(request):
    court_id = request.GET.get('court_id')
    booking_date = request.GET.get('date')
    if not court_id or not booking_date:
        return JsonResponse({'success': False, 'errors': ['Missing parameters']}, status=400)

    court = get_object_or_404(Court, pk=court_id, is_active=True)
    try:
        booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'success': False, 'errors': ['Invalid date supplied']}, status=400)

    now = timezone.localtime()
    slots = [_build_slot_payload(court, slot_start, now) for slot_start in _slot_range(court, booking_date)]
    return JsonResponse({'success': True, 'data': {'slots': slots}})


@login_required
@require_POST
def api_toggle_favorite(request):
    payload = {}
    if request.body:
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            payload = {}
    court_id = payload.get('court_id') or request.POST.get('court_id')
    if not court_id:
        return JsonResponse({'success': False, 'errors': ['Missing court id']}, status=400)
    court = get_object_or_404(Court, pk=court_id, is_active=True)
    favorite, created = FavoriteCourt.objects.get_or_create(user=request.user, court=court)
    if not created:
        favorite.delete()
        message = 'Removed from favorites.'
        is_favorite = False
    else:
        message = 'Court added to favorites.'
        is_favorite = True
    return JsonResponse({'success': True, 'data': {'message': message, 'is_favorite': is_favorite}})
