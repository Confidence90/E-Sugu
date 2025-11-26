# payments/admin.py
from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'listing', 'buyer', 'seller', 'amount', 'commission', 'status', 'created_at']
    search_fields = ['listing__title', 'buyer__name', 'seller__name']