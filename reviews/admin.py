# reviews/admin.py
from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'reviewer', 'reviewed', 'rating', 'comment', 'created_at']
    search_fields = ['reviewer__name', 'reviewed__name', 'comment']