from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("login/", views.show_login, name="login"),
    path("register/", views.show_register, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("venue/<slug:slug>/", views.product_detail, name="product_detail"),
    path("venue/<slug:slug>/wishlist/", views.toggle_wishlist, name="toggle_wishlist"),
    path("venue/<slug:slug>/booking/", views.booking_times, name="booking_times"),
    path("booking/<int:booking_id>/payment/", views.booking_payment, name="booking_payment"),
    path("booking/<int:booking_id>/success/", views.booking_success, name="booking_success"),
]
