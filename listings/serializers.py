# listings/serializers.py
from rest_framework import serializers
from .models import Listing, Image
from categories.models import Category
from notifications.models import Notification 
from commandes.models import Order

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image', 'created_at']

class ListingSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory = serializers.SerializerMethodField()
    available_quantity = serializers.ReadOnlyField()  # 🔥 NOUVEAU
    is_out_of_stock = serializers.ReadOnlyField()  
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'description', 'price', 'type', 'condition', 'status',
            'location', 'category', 'category_name', 'subcategory', 'user',
            'is_featured', 'images', 'created_at', 'updated_at',
            'quantity', 'quantity_sold', 'available_quantity', 'is_out_of_stock'  # 🔥 NOUVEAU
        ]
        read_only_fields = ['quantity_sold', 'available_quantity', 'is_out_of_stock', 'status']
    def validate_category(self, value):
        if not Category.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Catégorie non trouvée.")
        return value
    def get_subcategory(self, obj):
        if obj.category and obj.category.parent:
            return obj.category.name
        return None

class ListingCreateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )
    quantity = serializers.IntegerField(min_value=1, default=1)
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'price', 'type', 'condition', 'location',
            'category', 'images', 'is_featured', 'quantity'
        ]
    def validate(self, attrs):
        # 🔥 VÉRIFICATION DU STATUT VENDEUR
        user = self.context['request'].user
        if not user.can_create_listing():
            raise serializers.ValidationError({
                'non_field_errors': [
                    "Vous devez être un vendeur vérifié pour publier des annonces. "
                    "Complétez votre profil vendeur et attendez la validation."
                ]
            })
        return attrs

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        user = self.context['request'].user
        if not user.can_create_listing():
            raise serializers.ValidationError("Statut vendeur invalide.")
        listing = Listing.objects.create(**validated_data, user=self.context['request'].user)
        for image in images:
            Image.objects.create(listing=listing, image=image)
        return listing
    def validate_category(self, value):
        if not Category.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Catégorie invalide ou inexistante.")
        return value


class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['image']
class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['listing', 'quantity', 'shipping_address', 'customer_notes']

    def validate(self, data):
        listing = data['listing']
        quantity = data['quantity']
        
        # Vérifier la disponibilité
        if quantity > listing.available_quantity:
            raise serializers.ValidationError({
                'quantity': f'Quantité demandée non disponible. Stock restant: {listing.available_quantity}'
            })
        
        if listing.is_out_of_stock:
            raise serializers.ValidationError({
                'listing': 'Ce produit est actuellement épuisé.'
            })
            
        return data