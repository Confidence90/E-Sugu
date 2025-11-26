from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Panier, PanierItem
from .serializers import PanierSerializer, PanierItemSerializer, PanierItemCreateSerializer
from listings.models import Listing


class PanierViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer le panier d'achat
    """
    serializer_class = PanierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retourne le panier de l'utilisateur connecté
        """
        return Panier.objects.filter(user=self.request.user).prefetch_related('items__listing')
    

    def get_or_create_panier(self):
        """
        Récupère ou crée un panier pour l'utilisateur connecté
        """
        panier, created = Panier.objects.get_or_create(user=self.request.user)
        return panier

    def list(self, request, *args, **kwargs):
        """
        Affiche le panier de l'utilisateur
        """
        panier = self.get_or_create_panier()
        serializer = self.get_serializer(panier)
        return Response(serializer.data)
        try:
            panier = self.get_or_create_panier()
            serializer = self.get_serializer(panier)
            return Response(serializer.data)
        except Exception as e:
            print(f"❌ Erreur dans list: {str(e)}")
            return Response(
                {'error': 'Erreur serveur lors du chargement du panier'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        Ajoute un article au panier avec validation de stock
        """
        serializer = PanierItemCreateSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            listing_id = serializer.validated_data['listing_id']
            quantity = serializer.validated_data['quantity']

            try:
                listing = Listing.objects.get(id=listing_id)
            except Listing.DoesNotExist:
                return Response({'error': 'Produit non trouvé'}, status=status.HTTP_404_NOT_FOUND)

            panier = self.get_or_create_panier()
            try:
            # Vérifier si l'article est déjà dans le panier
                panier_item, created = PanierItem.objects.get_or_create(
                    panier=panier,
                    listing=listing,
                    defaults={'quantity': quantity}
                )
                new_quantity = panier_item.quantity + quantity
                if new_quantity > listing.available_quantity:
                    available_to_add = listing.available_quantity - panier_item.quantity
                    if available_to_add <= 0:
                        return Response({
                            'error': f'Quantité maximale déjà atteinte. Stock disponible: {listing.available_quantity}'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    panier_item.quantity = listing.available_quantity
                    panier_item.save()
                    return Response({
                        'message': f'Quantité limitée au stock disponible: {listing.available_quantity}',
                        'limited_quantity': listing.available_quantity
                    }, status=status.HTTP_200_OK)
                else:
                    panier_item.quantity = new_quantity
                    panier_item.save()
                
            except PanierItem.DoesNotExist:
                # Nouvel article
                if quantity > listing.available_quantity:
                    return Response({
                        'error': f'Quantité demandée non disponible. Stock: {listing.available_quantity}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                panier_item = PanierItem.objects.create(
                    panier=panier,
                    listing=listing,
                    quantity=quantity
                )

            serializer = PanierItemSerializer(panier_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None, *args, **kwargs):
        """
        Modifie la quantité d'un article dans le panier avec validation de stock
        """
        try:
            panier_item = PanierItem.objects.get(id=pk, panier__user=request.user)
        except PanierItem.DoesNotExist:
            return Response({'error': 'Article non trouvé dans le panier'}, status=status.HTTP_404_NOT_FOUND)

        quantity = request.data.get('quantity')
        if quantity is None:
            return Response({'error': 'La quantité est requise'}, status=status.HTTP_400_BAD_REQUEST)

        quantity = int(quantity)
        
        # 🔥 Validation de la quantité par rapport au stock disponible
        if quantity > panier_item.listing.available_quantity:
            return Response({
                'error': f'Quantité non disponible. Stock restant: {panier_item.listing.available_quantity}'
            }, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            # Si la quantité est 0 ou négative, supprimer l'article
            panier_item.delete()
            return Response({'message': 'Article supprimé du panier'}, status=status.HTTP_204_NO_CONTENT)

        panier_item.quantity = quantity
        panier_item.save()

        serializer = PanierItemSerializer(panier_item)
        return Response(serializer.data)

    def destroy(self, request, pk=None, *args, **kwargs):
        """
        Supprime un article du panier
        """
        try:
            panier_item = PanierItem.objects.get(id=pk, panier__user=request.user)
            panier_item.delete()
            return Response({'message': 'Article supprimé du panier'}, status=status.HTTP_204_NO_CONTENT)
        except PanierItem.DoesNotExist:
            return Response({'error': 'Article non trouvé'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Vider tout le panier"""
        panier = self.get_or_create_panier()
        count, _ = panier.items.all().delete()
        return Response({'message': f'{count} article(s) supprimé(s) du panier'})

    @action(detail=False, methods=['get'])
    def validate(self, request):
        """Valider le panier avant création de commande"""
        panier = self.get_or_create_panier()
        can_create, message = panier.can_create_order()
        
        return Response({
            'can_create_order': can_create,
            'message': message,
            'total_items': panier.items.count(),
            'total_price': panier.total_price()
        })


class PanierTotalView(APIView):
    """
    API View pour obtenir le prix total du panier
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Calcule le prix total du panier
        """
        try:
            panier = Panier.objects.get(user=request.user)
            total = panier.total_price()
            item_count = panier.items.count()
            can_create, validation_message = panier.can_create_order()
            return Response({
                'total_price': float(total),
                'item_count': item_count,
                'can_create_order': can_create,
                'validation_message': validation_message,
                'message': f'Panier avec {item_count} article(s)'
            })
        except Panier.DoesNotExist:
            return Response({
                'total_price': 0,
                'item_count': 0,
                'can_create_order': False,
                'validation_message': 'Le panier est vide',
                'message': 'Panier vide'
            })