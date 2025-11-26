from rest_framework import serializers
from .models import Order, OrderItem
from listings.serializers import ListingSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['listing', 'quantity', 'price', 'subtotal']

    subtotal = serializers.SerializerMethodField()

    def get_subtotal(self, obj):
        return obj.subtotal()

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    order_number = serializers.CharField(read_only=True)
    pending_since = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user', 'status', 'total_price', 
                 'payment_method', 'shipping_method', 'shipping_country',
                 'is_packaged', 'created_at', 'pending_since', 'items']
    
    def get_payment_method(self, obj):
        return obj.payment_method()
    
    def get_pending_since(self, obj):
        return obj.pending_since()
