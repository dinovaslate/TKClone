from django.contrib import admin

from .models import AddOn, Booking, Category, Review, Venue, WishlistEntry


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "category", "price_per_hour")
    list_filter = ("city", "category")
    search_fields = ("name", "city")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ("name", "price")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("venue", "user", "rating", "created_at")
    list_filter = ("rating", "venue")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("venue", "user", "date", "time_slot", "status", "total_price")
    list_filter = ("status", "payment_method", "date")
    search_fields = ("venue__name", "user__username")


@admin.register(WishlistEntry)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "venue", "created_at")
