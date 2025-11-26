from rest_framework import serializers
from .models import Panier, PanierItem
from listings.serializers import ListingSerializer
from listings.models import Listing

class PanierItemCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour l'ajout d'articles au panier"""
    listing_id = serializers.IntegerField()

    class Meta:
        model = PanierItem
        fields = ['listing_id', 'quantity']
    def validate(self, data):
        listing_id = data.get('listing_id')
        quantity = data.get('quantity', 1)
        
        try:
            listing = Listing.objects.get(id=listing_id)
        except Listing.DoesNotExist:
            raise serializers.ValidationError({"listing_id": "Produit non trouvé"})
        
        # 🔥 Vérifier la disponibilité du stock
        if listing.is_out_of_stock:
            raise serializers.ValidationError({"listing": "Ce produit est épuisé"})
        
        if quantity > listing.available_quantity:
            raise serializers.ValidationError({
                "quantity": f"Quantité non disponible. Stock restant: {listing.available_quantity}"
            })
        
        # Vérifier que l'utilisateur n'achète pas son propre produit
        if self.context['request'].user == listing.user:
            raise serializers.ValidationError({
                "listing": "Vous ne pouvez pas ajouter votre propre produit au panier"
            })
        
        return data

class PanierItemSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    is_available = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    available_quantity = serializers.ReadOnlyField()

    class Meta:
        model = PanierItem
        fields = ['id', 'listing', 'quantity', 'added_at', 'total_price', 'is_available', 'available_quantity']
        read_only_fields = ['id', 'added_at', 'total_price', 'is_available', 'available_quantity']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['total_price'] = instance.total_price()
        data['is_available'] = instance.is_available()
        data['available_quantity'] = instance.listing.available_quantity
        return data
    def get_total_price(self, obj):
        """Calcule le total pour cet article"""
        if obj.listing and hasattr(obj.listing, 'price'):
            return obj.quantity * obj.listing.price
        return 0

    def get_is_available(self, obj):
        """Vérifie si le produit est encore disponible"""
        if obj.listing:
            return obj.listing.is_available if hasattr(obj.listing, 'is_available') else True
        return False

class PanierSerializer(serializers.ModelSerializer):
    items = PanierItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    can_create_order = serializers.SerializerMethodField()
    validation_message = serializers.SerializerMethodField()

    class Meta:
        model = Panier
        fields = ['id', 'user', 'created_at', 'items', 'total_price', 'can_create_order', 'validation_message']
        read_only_fields = ['id', 'user', 'created_at']

    def get_total_price(self, obj):
        return obj.total_price()
    def get_can_create_order(self, obj):
        """Vérifie si une commande peut être créée depuis ce panier"""
        can_create, _ = obj.can_create_order()
        return can_create
    
    def get_validation_message(self, obj):
        """Message de validation pour la création de commande"""
        _, message = obj.can_create_order()
        return message