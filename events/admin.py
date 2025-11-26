# events/admin.py
from django.contrib import admin
from .models import Event, EventListing, EventMessage

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'start_time', 'status', 'user', 'created_at']
    search_fields = ['title', 'description']

@admin.register(EventListing)
class EventListingAdmin(admin.ModelAdmin):
    list_display = ['id', 'event', 'listing', 'special_offer']

@admin.register(EventMessage)
class EventMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'event', 'sender', 'content', 'timestamp']