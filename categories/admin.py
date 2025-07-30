# categories/admin.py
from django.contrib import admin
from .models import Category

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'parent_name', 'has_children')
    list_filter = ('parent',)
    search_fields = ('name','parent__name')

    def parent_name(self, obj):
        return obj.parent.name if obj.parent else '-'
    parent_name.short_description = 'Parent'

    def has_children(self, obj):
        return obj.subcategories.exists()
    has_children.boolean = True
    has_children.short_description = 'A des sous-catégories ?'

admin.site.register(Category, CategoryAdmin)