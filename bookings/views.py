from __future__ import annotations

import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from courts.models import Court

from .models import Booking
from payments.services import process_mock_payment


@login_required
def dashboard(request):
    return render(request, 'bookings/dashboard.html')


def _parse_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body)
    except json.JSONDecodeError:
        return {}


def _serialize_booking(booking: Booking):
    return {
        'id': booking.id,
        'court_name': booking.court.name,
        'date': booking.date.isoformat(),
        'start_time': booking.start_time.strftime('%H:%M'),
        'end_time': booking.end_time.strftime('%H:%M'),
        'status': booking.status,
        'payment_status': booking.payment_status,
        'total_price': float(booking.total_price),
        'hold_expires_at': booking.hold_expires_at.isoformat() if booking.hold_expires_at else None,
    }


@login_required
@require_POST
def api_create_booking(request):
    payload = _parse_json(request)
    for field in ('court_id', 'date', 'start_time', 'end_time'):
        if not payload.get(field):
            return JsonResponse({'success': False, 'errors': [f'Missing field: {field}']}, status=400)

    court = get_object_or_404(Court, pk=payload['court_id'], is_active=True)
    try:
        booking_date = datetime.strptime(payload['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(payload['start_time'], '%H:%M').time()
        end_time = datetime.strptime(payload['end_time'], '%H:%M').time()
    except ValueError:
        return JsonResponse({'success': False, 'errors': ['Invalid datetime payload']}, status=400)

    with transaction.atomic():
        _ = (
            Booking.objects.select_for_update()
            .filter(court=court, date=booking_date)
            .exists()
        )
        booking = Booking(
            user=request.user,
            court=court,
            date=booking_date,
            start_time=start_time,
            end_time=end_time,
        )
        try:
            booking.full_clean()
        except ValidationError as exc:
            return JsonResponse({'success': False, 'errors': exc.messages}, status=400)
        booking.save()

    hold_seconds = max(0, int((booking.hold_expires_at - timezone.now()).total_seconds()))
    minutes = hold_seconds // 60
    seconds = hold_seconds % 60
    countdown = f"{minutes:02d}:{seconds:02d}"

    return JsonResponse(
        {
            'success': True,
            'data': {
                'message': f'Booking held for {booking.start_time.strftime("%H:%M")}-{booking.end_time.strftime("%H:%M")}. Expires in {countdown}.',
                'booking': _serialize_booking(booking),
            },
        }
    )


@login_required
@require_GET
def api_my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    data = [_serialize_booking(booking) for booking in bookings]
    return JsonResponse({'success': True, 'data': {'results': data}})


@login_required
@require_POST
def api_confirm_booking(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if booking.status != Booking.STATUS_PENDING:
        return JsonResponse({'success': False, 'errors': ['Only pending bookings can be confirmed.']}, status=400)
    payment = process_mock_payment(float(booking.total_price))
    booking.confirm()
    receipt_url = reverse('payments:receipt', args=[booking.id])
    return JsonResponse(
        {
            'success': True,
            'data': {
                'message': 'Booking confirmed and payment recorded.',
                'receipt_url': receipt_url,
                'reference': payment.reference,
            },
        }
    )


@login_required
@require_POST
def api_cancel_booking(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    payload = _parse_json(request)
    if payload.get('undo'):
        booking.restore()
        return JsonResponse({'success': True, 'data': {'message': 'Booking restored.'}})

    if booking.status == Booking.STATUS_CANCELED:
        return JsonResponse({'success': False, 'errors': ['Booking already canceled.']}, status=400)
    booking.cancel()
    return JsonResponse({'success': True, 'data': {'message': 'Booking canceled. You can undo for a few seconds.'}})
