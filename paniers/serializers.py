from rest_framework import serializers
from .models import Panier, PanierItem
from listings.serializers import ListingSerializer


class PanierItemSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = PanierItem
        fields = ['id', 'listing', 'quantity', 'added_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['total_price'] = instance.total_price()
        return data


class PanierSerializer(serializers.ModelSerializer):
    items = PanierItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Panier
        fields = ['id', 'user', 'created_at', 'items', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price()
