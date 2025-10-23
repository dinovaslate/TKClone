from django.contrib import admin

from .models import AddOn, Booking, BookingAddOn, Category, City, Review, TimeSlot, Venue, VenuePhoto, WishlistEntry


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


class VenuePhotoInline(admin.TabularInline):
    model = VenuePhoto
    extra = 1


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "category", "price_per_hour")
    list_filter = ("city", "category")
    search_fields = ("name", "city__name", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [VenuePhotoInline]


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ("venue", "date", "start_time", "end_time", "is_booked")
    list_filter = ("venue", "date", "is_booked")


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ("name", "price")
    filter_horizontal = ("venues",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "venue", "time_slot", "status", "payment_method")
    list_filter = ("status", "payment_method")
    search_fields = ("user__username", "venue__name")


@admin.register(BookingAddOn)
class BookingAddOnAdmin(admin.ModelAdmin):
    list_display = ("booking", "addon", "quantity")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "venue", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "venue__name", "comment")


@admin.register(WishlistEntry)
class WishlistEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "venue", "created_at")
    search_fields = ("user__username", "venue__name")
