# payments/serializers.py
from rest_framework import serializers
from .models import Transaction
from listings.serializers import ListingSerializer
from users.serializers import UserProfileSerializer

class TransactionSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    buyer_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'listing', 'listing_title', 'buyer', 'buyer_name', 
            'seller', 'seller_name', 'amount', 'quantity', 'total_amount','commission', 'net_amount', 
            'status', 'payment_method', 'stripe_payment_intent_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['buyer', 'seller', 'commission', 'net_amount']

class CreateTransactionSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField(required=False)
    payment_method = serializers.CharField()
    payment_token = serializers.CharField(required=False)  # Pour Stripe Elements

    def validate(self, data):
        """
        Valider qu'au moins listing_id ou panier est fourni
        """
        listing_id = data.get('listing_id')
        
        if not listing_id:
            # Vérifier que l'utilisateur a un panier non vide
            from paniers.models import Panier  # Ensure 'cart' is in INSTALLED_APPS and the path is correct
            try:
                panier = Panier.objects.get(user=self.context['request'].user)
                if not panier.items.exists():
                    raise serializers.ValidationError("Le panier est vide. Ajoutez des articles ou spécifiez un listing_id.")
            except Panier.DoesNotExist:
                raise serializers.ValidationError("Panier non trouvé. Ajoutez des articles ou spécifiez un listing_id.")
        
        return data

    def validate_payment_method(self, value):
        valid_methods = ['card', 'orange_money', 'moov_money']
        if value not in valid_methods:
            raise serializers.ValidationError("Méthode de paiement non supportée")
        return value

class PaymentConfirmationSerializer(serializers.Serializer):
    payment_intent_id = serializers.CharField()
    payment_method_id = serializers.CharField(required=False)