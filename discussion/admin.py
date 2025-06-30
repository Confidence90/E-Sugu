# messages/admin.py
from django.contrib import admin
from .models import Message


class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'discussion', 'sender', 'content', 'created_at']
    search_fields = ['content', 'sender__username']
    list_filter = ['created_at', 'sender']

admin.site.register(Message, MessageAdmin)