# payments/serializers.py
from rest_framework import serializers
from .models import Transaction
from listings.serializers import ListingSerializer
from users.serializers import UserProfileSerializer

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

    class Meta:
        model = Transaction
        fields = ['id', 'listing', 'buyer', 'seller', 'amount', 'commission', 'net_amount', 'status', 'payment_method', 'created_at']

class CreateTransactionSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField()
    payment_method = serializers.CharField()