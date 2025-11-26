# listings/views.py
from rest_framework import viewsets, status, filters
from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Listing, Image, ListingView
from commandes.models import Order
from rest_framework.exceptions import ValidationError
from .serializers import ListingSerializer, ImageUploadSerializer, ListingCreateSerializer, OrderCreateSerializer
from categories.models import Category
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ListingFilter
from rest_framework.pagination import PageNumberPagination
from notifications.models import Notification
import random
from .permissions import IsSellerPermission 
from django.db import models, transaction
import logging
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

def get_all_subcategories(category):
    """
    Récupère récursivement toutes les sous-catégories d'une catégorie donnée.
    """
    subcategories = []
    for subcat in category.subcategories.all():
        subcategories.append(subcat)
        subcategories.extend(get_all_subcategories(subcat))
    return subcategories
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 40
    page_size_query_param = 'page_size'
    max_page_size = 100



class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.filter(status='active')
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at'] 

    def get_serializer_class(self):
        if self.action == 'create':
            return ListingCreateSerializer
        return ListingSerializer
    

    # listings/views.py

    


    def get_queryset(self):
        queryset = super().get_queryset()
        category_name = self.request.query_params.get('category')
        my_listings = self.request.query_params.get('my_listings')
        if my_listings and self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        
        category_name = self.request.query_params.get('category')
        if category_name:
            try:
                category = Category.objects.get(name=category_name)

                # Fonction récursive pour récupérer toutes les sous-catégories
                def get_all_subcategories(cat):
                    subs = cat.subcategories.all()
                    all_subs = list(subs)
                    for sub in subs:
                        all_subs.extend(get_all_subcategories(sub))
                    return all_subs

                # Inclure la catégorie et toutes ses sous-catégories
                all_categories = [category] + get_all_subcategories(category)

                # On filtre par leurs noms
                category_names = [cat.name for cat in all_categories]
                queryset = queryset.filter(category__name__in=category_names)

            except Category.DoesNotExist:
                queryset = queryset.none()

        if self.action == 'featured':
            return queryset.filter(is_featured=True).order_by('?')

        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'upload_image']:
            return [IsAuthenticated()]
        elif self.action in ['mark_as_sold', 'deactivate', 'restock']:
            return [IsAuthenticated(), IsOwner()]
        return super().get_permissions()

    @action(detail=True, methods=['post'], url_path='images')
    def upload_image(self, request, pk=None):
        listing = self.get_object()
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            Image.objects.create(listing=listing, image=serializer.validated_data['image'])
            return Response({'message': 'Image ajoutée'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwner])
    def mark_as_sold(self, request, pk=None):
        listing = self.get_object()
        listing.mark_as_sold()
        return Response({'message': 'Annonce marquée comme vendue.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwner])
    def deactivate(self, request, pk=None):
        listing = self.get_object()
        listing.deactivate()
        return Response({'message': 'Annonce désactivée (expirée).'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True).order_by('?')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        listing = self.get_object()
        serializer = self.get_serializer(listing)
        return Response(serializer.data)
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def create_order(self, request, pk=None):
        listing = self.get_object()
        if listing.user == request.user:
            return Response({'error': "Vous ne pouvez pas acheter votre propre annonce."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    order = Order.objects.create(
                        listing=listing,
                        buyer=request.user,
                        **serializer.validated_data
                    )
                    if order.confirmed:
                        Notification.objects.create(
                            user=listing.user,
                            type = 'order',
                            content=f'Nouvelle commande pour "{listing.title}" - Quantité: {order.quantity}')
                        if listing.is_out_of_stock:
                            # 🔥 NOTIFICATION d'épuisement de stock
                            Notification.objects.create(
                                user=listing.user,
                                type='listing',
                                content=f'Votre produit "{listing.title}" est maintenant épuisé.'
                            )
                        
                        return Response({
                            'message': 'Commande créée avec succès',
                            'order_id': order.id
                        }, status=status.HTTP_201_CREATED)
                    else:
                        return Response({
                            'error': 'Quantité non disponible'
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def restock(self, request, pk=None):
        """Réapprovisionner le produit (pour le vendeur)"""
        listing = self.get_object()
        
        # Vérifier que l'utilisateur est le vendeur
        if listing.user != request.user:
            return Response(
                {'error': 'Vous ne pouvez modifier que vos propres annonces.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_quantity = request.data.get('quantity')
        if not new_quantity or not isinstance(new_quantity, int) or new_quantity <= 0:
            return Response(
                {'error': 'Quantité invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        listing.restock(new_quantity)
        
        # 🔥 NOTIFICATION si le produit était épuisé et est maintenant disponible
        if listing.status == 'active' and listing.available_quantity > 0:
            Notification.objects.create(
                user=listing.user,
                type='listing',
                content=f'Votre produit "{listing.title}" est maintenant disponible en stock.'
            )
        
        serializer = self.get_serializer(listing)
        return Response(serializer.data)
    def create(self, request, *args, **kwargs):
        print("🔍 CREATE action appelée")
        print(f"👤 Utilisateur: {request.user}")
        print(f"🔐 Authentifié: {request.user.is_authenticated}")
        print(f"📦 Données: {request.data}")
        if not request.user.can_create_listing():
            return Response(
                {
                    'error': 'Accès refusé. Seuls les vendeurs vérifiés peuvent publier des annonces.',
                    'solution': 'Complétez votre profil vendeur et attendez la validation.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

# 🔥 NOUVEAU : ViewSet pour les commandes
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderCreateSerializer
    
    def get_queryset(self):
        # Les utilisateurs voient seulement leurs commandes (acheteur) ou leurs ventes (vendeur)
        user = self.request.user
        return Order.objects.filter(
            models.Q(buyer=user) | models.Q(listing__user=user)
        ).distinct()
    
    def create(self, request, *args, **kwargs):
        # Utiliser l'endpoint spécifique dans ListingViewSet pour créer des commandes
        return Response(
            {'error': 'Utilisez l\'endpoint /api/listings/{id}/create_order/'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm(self, request, pk=None):
        """Confirmer une commande (pour le vendeur)"""
        order = self.get_object()
        
        # Vérifier que l'utilisateur est le vendeur
        if order.listing.user != request.user:
            return Response(
                {'error': 'Seul le vendeur peut confirmer cette commande.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.confirm_order():
            return Response({'message': 'Commande confirmée avec succès'})
        else:
            return Response(
                {'error': 'Impossible de confirmer la commande'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Annuler une commande"""
        order = self.get_object()
        
        # Vérifier que l'utilisateur est l'acheteur ou le vendeur
        if order.buyer != request.user and order.listing.user != request.user:
            return Response(
                {'error': 'Vous ne pouvez pas annuler cette commande.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.cancel_order():
            return Response({'message': 'Commande annulée avec succès'})
        else:
            return Response(
                {'error': 'Impossible d\'annuler la commande'},
                status=status.HTTP_400_BAD_REQUEST
            )

logger = logging.getLogger(__name__)

# listings/views.py - Corrigez track_listing_view

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def track_listing_view(request, listing_id):
    """Suivre une vue sur une annonce"""
    try:
        listing = Listing.objects.get(id=listing_id)
        
        # Récupérer les informations de la requête
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # 🔥 CORRECTION: Gérer les sessions de manière sécurisée
        session_key = None
        if hasattr(request, 'session') and request.session.session_key:
            session_key = request.session.session_key
        else:
            # Créer une session si elle n'existe pas
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
        
        # Vérifier si c'est une vue unique
        user = request.user if request.user.is_authenticated else None
        
        # 🔥 CORRECTION: Vérifier si cette vue a déjà été comptabilisée récemment
        # (éviter les doublons pour la même IP/session dans un court délai)
        from datetime import timedelta
        recent_view = ListingView.objects.filter(
            listing=listing,
            ip_address=ip_address,
            viewed_at__gte=timezone.now() - timedelta(minutes=30)
        ).exists()
        
        if not recent_view:
            # Créer un enregistrement de vue détaillé
            ListingView.objects.create(
                listing=listing,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                session_key=session_key
            )
            
            # Incrémenter les compteurs dans le modèle Listing
            listing.increment_views(user)
        
        return Response({
            'status': 'success',
            'listing_id': listing.id,
            'views_count': listing.views_count,
            'unique_visitors': listing.unique_visitors
        }, status=status.HTTP_200_OK)
        
    except Listing.DoesNotExist:
        return Response({'error': 'Annonce non trouvée'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur suivi vue: {str(e)}")
        return Response({'error': 'Erreur interne'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
def get_client_ip(request):
    """Récupérer l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# listings/views.py - Ajoutez cette vue de test

@api_view(['GET'])
@permission_classes([AllowAny])
def test_tracking_view(request, listing_id):
    """Vue de test pour vérifier le tracking"""
    try:
        listing = Listing.objects.get(id=listing_id)
        
        # Simuler une vue
        from listings.models import ListingView
        
        # Récupérer les informations de la requête
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        session_key = request.session.session_key
        
        # Vérifier si c'est une vue unique
        user = request.user if request.user.is_authenticated else None
        
        # Créer un enregistrement de vue détaillé
        listing_view = ListingView.objects.create(
            listing=listing,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            session_key=session_key
        )
        
        # Incrémenter les compteurs dans le modèle Listing
        listing.increment_views(user)
        
        return Response({
            'status': 'success',
            'listing_id': listing.id,
            'listing_title': listing.title,
            'current_views': listing.views_count,
            'current_unique_visitors': listing.unique_visitors,
            'view_id': listing_view.id,
            'ip_address': ip_address
        }, status=status.HTTP_200_OK)
        
    except Listing.DoesNotExist:
        return Response({'error': 'Annonce non trouvée'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Erreur test tracking: {str(e)}")
        return Response({'error': 'Erreur interne'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)