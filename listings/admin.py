# listings/admin.py
from django.contrib import admin
from .models import Listing, Image

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'price', 'category', 'status', 'user', 'created_at']
    search_fields = ['title', 'description']

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'image', 'created_at']