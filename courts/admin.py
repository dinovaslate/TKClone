from django.contrib import admin

from .models import Court, FavoriteCourt, MaintenanceBlock


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('name', 'surface_type', 'location', 'price_per_hour', 'is_active')
    search_fields = ('name', 'location')
    list_filter = ('surface_type', 'is_active')


@admin.register(MaintenanceBlock)
class MaintenanceBlockAdmin(admin.ModelAdmin):
    list_display = ('court', 'start_dt', 'end_dt', 'reason')
    list_filter = ('court',)


@admin.register(FavoriteCourt)
class FavoriteCourtAdmin(admin.ModelAdmin):
    list_display = ('user', 'court', 'created_at')
    autocomplete_fields = ('user', 'court')
