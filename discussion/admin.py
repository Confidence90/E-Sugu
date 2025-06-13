# messages/admin.py
from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'receiver', 'listing', 'content', 'timestamp']
    search_fields = ['sender__name', 'receiver__name', 'content']