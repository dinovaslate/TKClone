from django.urls import path

from . import views

app_name = "main"


urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("home/", views.home_view, name="home"),
    path("catalog/", views.catalog_view, name="catalog"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("wishlist/<int:venue_id>/toggle/", views.toggle_wishlist, name="toggle_wishlist"),
    path("venues/<slug:slug>/", views.venue_detail, name="venue_detail"),
    path("venues/<slug:slug>/booking/", views.booking_schedule, name="booking_schedule"),
    path("booking/<int:pk>/payment/", views.payment_view, name="payment"),
    path("booking/<int:pk>/payment/success/", views.payment_success, name="payment_success"),
]
