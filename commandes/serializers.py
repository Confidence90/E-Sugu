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

# commandes/serializers.py - AJOUTER
class VendorOrderSerializer(serializers.ModelSerializer):
    buyer = serializers.SerializerMethodField()
    vendor_items = serializers.SerializerMethodField()
    vendor_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'buyer', 'vendor_items', 
            'vendor_total', 'status', 'created_at', 'is_packaged'
        ]
    
    def get_buyer(self, obj):
        return {
            'name': obj.user.get_full_name(),
            'email': obj.user.email,
            'phone': obj.user.phone
        }
    
    def get_vendor_items(self, obj):
        request = self.context.get('request')
        vendor_items = obj.items.filter(listing__user=request.user)
        return OrderItemSerializer(vendor_items, many=True).data
    
    def get_vendor_total(self, obj):
        request = self.context.get('request')
        vendor_items = obj.items.filter(listing__user=request.user)
        return sum(item.subtotal() for item in vendor_items)