
from django.contrib import admin
from .models import FavoriteListing, FavoriteEvent

@admin.register(FavoriteListing)
class FavoriteListingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'listing']
    search_fields = ['user__name', 'listing__title']

@admin.register(FavoriteEvent)
class FavoriteEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'event']
    search_fields = ['user__username', 'event__title']