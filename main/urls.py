from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("login/", views.show_login, name="login"),
    path("register/", views.show_register, name="register"),
    path("logout/", views.logged_out, name="logout"),
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/<slug:slug>/toggle/", views.toggle_wishlist, name="toggle_wishlist"),
    path("venues/<slug:slug>/", views.product_detail, name="product_detail"),
    path(
        "venues/<slug:slug>/schedule/<slug:date_str>/",
        views.booking_schedule,
        name="booking_schedule",
    ),
    path("venues/<slug:slug>/book/<int:slot_id>/", views.book_slot, name="book_slot"),
    path("bookings/<int:booking_id>/payment/", views.payment_page, name="payment"),
    path(
        "bookings/<int:booking_id>/payment/waiting/",
        views.payment_waiting,
        name="payment_waiting",
    ),
    path(
        "bookings/<int:booking_id>/payment/success/",
        views.payment_success,
        name="payment_success",
    ),
]
