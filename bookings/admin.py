from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('court', 'user', 'date', 'start_time', 'end_time', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'court')
    search_fields = ('user__username', 'court__name')
    ordering = ('-created_at',)
