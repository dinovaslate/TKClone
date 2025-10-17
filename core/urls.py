from django.urls import path

from bookings import views as booking_views
from courts import views as court_views

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/courts', court_views.api_courts, name='api-courts'),
    path('api/availability', court_views.api_availability, name='api-availability'),
    path('api/favorites/toggle', court_views.api_toggle_favorite, name='api-favorites-toggle'),
    path('api/bookings', booking_views.api_create_booking, name='api-bookings-create'),
    path('api/bookings/mine', booking_views.api_my_bookings, name='api-bookings-mine'),
    path('api/bookings/<int:booking_id>/confirm', booking_views.api_confirm_booking, name='api-bookings-confirm'),
    path('api/bookings/<int:booking_id>/cancel', booking_views.api_cancel_booking, name='api-bookings-cancel'),
]
