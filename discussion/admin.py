from django.contrib import admin
from .models import Discussion, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender', 'content', 'created_at']

@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'title', 
        'participant1', 
        'participant2', 
        'discussion_type', 
        'is_active', 
        'created_at', 
        'updated_at'
    ]  # ✅ SUPPRIMEZ 'listing' de list_display
    
    list_filter = [
        'discussion_type', 
        'is_active', 
        'created_at'
    ]  # ✅ PAS de 'listing' ici non plus
    
    search_fields = [
        'title', 
        'participant1__username', 
        'participant2__username'
    ]  # ✅ SUPPRIMEZ 'listing__title'
    
    list_editable = ['is_active']
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'get_discussion_title',  # ✅ Utilisez une méthode personnalisée
        'sender', 
        'content_preview', 
        'is_read', 
        'created_at'
    ]
    
    list_filter = ['is_read', 'created_at', 'sender']
    search_fields = [
        'content', 
        'sender__username', 
        'discussion__title'  # ✅ Recherche par titre de discussion
    ]
    
    def get_discussion_title(self, obj):
        """Afficher le titre de la discussion"""
        return obj.discussion.title or f"Discussion {obj.discussion.id}"
    get_discussion_title.short_description = 'Discussion'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenu'