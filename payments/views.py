from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from bookings.models import Booking


@login_required
def receipt(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'payments/receipt.html', {'booking': booking})
