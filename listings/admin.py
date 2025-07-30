# listings/admin.py
from django.contrib import admin
from .models import Listing, Image

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'price', 'category', 'status', 'user', 'is_featured', 'created_at']
    search_fields = ['title', 'description']
    list_filter = ['category', 'status', 'type', 'is_featured']

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'image', 'created_at']