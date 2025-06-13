# users/admin.py
from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'phone_full', 'is_active', 'is_staff', 'created_at']
    search_fields = ['name', 'email', 'phone_full']