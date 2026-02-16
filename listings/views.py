# listings/views.py
from rest_framework import viewsets, status, filters
from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Listing, Image, ListingView
from commandes.models import Order
from rest_framework.permissions import IsAdminUser
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
    def get_object(self):
        """
        Permet à certaines actions de récupérer n'importe quelle annonce,
        pas seulement celles avec status='active'.
        """
        if self.action in ['update_listing', 'delete_listing', 'restock', 'toggle_status']:
            return Listing.objects.get(pk=self.kwargs['pk'])
        return super().get_object()

    


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
        # Vérifier si le produit était épuisé avant le réapprovisionnement
        was_out_of_stock = listing.is_out_of_stock
        listing.restock(new_quantity)
        
        # 🔥 NOTIFICATION si le produit était épuisé et est maintenant disponible
        #if listing.status == 'active' and listing.available_quantity > 0:
        #    Notification.objects.create(
        #        user=listing.user,
        #        type='listing',
         #       content=f'Votre produit "{listing.title}" est maintenant disponible en stock.'
        #    )
        if was_out_of_stock and listing.available_quantity > 0:
            listing.send_restock_notification()
        
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
    
    @action(detail=True, methods=['put', 'patch'], url_path='update',
            permission_classes=[IsAuthenticated, IsOwner])
    def update_listing(self, request, pk=None):
        """
        Mettre à jour une annonce (PUT pour remplacement complet, PATCH pour partiel)
        """
        listing = self.get_object()
        
        # Vérifier que le vendeur peut modifier cette annonce
        if listing.user != request.user:
            return Response(
                {'error': 'Vous ne pouvez modifier que vos propres annonces.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Utiliser le serializer approprié
        serializer = ListingCreateSerializer(
            listing,
            data=request.data,
            partial=request.method == 'PATCH',
            context={'request': request}
        )
        
        if serializer.is_valid():
            updated_listing = serializer.save()
            
            # Gérer les nouvelles images si présentes
            if 'images' in request.data and request.data['images']:
                # Supprimer les anciennes images ? (optionnel)
                # listing.images.all().delete()
                
                # Ajouter les nouvelles images
                for image in request.data.getlist('images'):
                    Image.objects.create(listing=updated_listing, image=image)
            
            return Response({
                'message': 'Annonce mise à jour avec succès',
                'listing': ListingSerializer(updated_listing).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], 
            permission_classes=[IsAuthenticated, IsOwner])
    def delete_listing(self, request, pk=None):
        """
        Supprimer une annonce
        """
        listing = self.get_object()
        
        # Vérifier que le vendeur peut supprimer cette annonce
        if listing.user != request.user:
            return Response(
                {'error': 'Vous ne pouvez supprimer que vos propres annonces.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier s'il y a des commandes en cours
        pending_orders = listing.orders.filter(
            status__in=['pending', 'confirmed', 'shipped']
        ).exists()
        
        if pending_orders:
            return Response({
                'error': 'Impossible de supprimer cette annonce car elle a des commandes en cours.',
                'solution': 'Désactivez l\'annonce plutôt que de la supprimer.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Sauvegarder le titre pour le message de confirmation
        title = listing.title
        
        # Supprimer l'annonce
        listing.delete()
        
        return Response({
            'message': f'Annonce "{title}" supprimée avec succès',
            'success': True
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], 
            permission_classes=[IsAuthenticated])
    def bulk_delete(self, request):
        """
        Supprimer plusieurs annonces en masse
        """
        listing_ids = request.data.get('listing_ids', [])
        
        if not listing_ids:
            return Response({
                'error': 'Aucune annonce sélectionnée'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtrer uniquement les annonces de l'utilisateur
        listings = Listing.objects.filter(
            id__in=listing_ids,
            user=request.user
        )
        
        # Vérifier les commandes en cours
        for listing in listings:
            if listing.orders.filter(
                status__in=['pending', 'confirmed', 'shipped']
            ).exists():
                return Response({
                    'error': f'L\'annonce "{listing.title}" a des commandes en cours et ne peut pas être supprimée.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        count = listings.count()
        listings.delete()
        
        return Response({
            'message': f'{count} annonce(s) supprimée(s) avec succès',
            'count': count
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], 
            permission_classes=[IsAuthenticated, IsOwner])
    def toggle_status(self, request, pk=None):
        """
        Activer/Désactiver une annonce
        """
        listing = self.get_object()
        
        if listing.user != request.user:
            return Response(
                {'error': 'Action non autorisée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        
        if new_status not in ['active', 'expired']:
            return Response({
                'error': 'Statut invalide. Utilisez "active" ou "expired".'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        listing.status = new_status
        listing.save()
        
        return Response({
            'message': f'Annonce {"activée" if new_status == "active" else "désactivée"} avec succès',
            'status': listing.status,
            'listing': ListingSerializer(listing).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], 
            permission_classes=[IsAuthenticated, IsOwner])
    def delete_image(self, request, pk=None):
        """
        Supprimer une image spécifique d'une annonce
        """
        listing = self.get_object()
        
        if listing.user != request.user:
            return Response(
                {'error': 'Action non autorisée'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response({
                'error': 'ID de l\'image requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            image = listing.images.get(id=image_id)
            image.delete()
            
            return Response({
                'message': 'Image supprimée avec succès',
                'listing': ListingSerializer(listing).data
            }, status=status.HTTP_200_OK)
            
        except Image.DoesNotExist:
            return Response({
                'error': 'Image non trouvée'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], 
            permission_classes=[IsAuthenticated])
    def my_listings(self, request):
        """
        Récupérer toutes les annonces du vendeur connecté
        """
        queryset = Listing.objects.filter(user=request.user)
        
        # Filtres optionnels
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Tri
        order_by = request.query_params.get('order_by', '-created_at')
        if order_by.lstrip('-') in ['title', 'price', 'created_at', 'status', 'views_count']:
            queryset = queryset.order_by(order_by)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
    
# listings/views.py - AJOUTEZ CES VUES
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_products_stats(request):
    """Statistiques des produits pour l'administration"""
    try:
        today = timezone.now()
        last_30_days = today - timedelta(days=30)
        
        # Statistiques de base
        total_products = Listing.objects.count()
        active_products = Listing.objects.filter(status='active').count()
        out_of_stock = Listing.objects.filter(status='out_of_stock').count()
        sold_out = Listing.objects.filter(status='sold').count()
        featured_products = Listing.objects.filter(is_featured=True).count()
        
        # Produits créés aujourd'hui
        new_products_today = Listing.objects.filter(created_at__date=today.date()).count()
        
        # Ventes et revenus (30 derniers jours)
        recent_orders = Order.objects.filter(
            created_at__gte=last_30_days,
            status='completed'
        )
        total_sales = recent_orders.count()
        total_revenue = recent_orders.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        # Prix moyen
        average_price = Listing.objects.filter(status='active').aggregate(
            avg=Avg('price')
        )['avg'] or 0
        
        # Catégorie la plus vue
        most_viewed_category = Listing.objects.values(
            'category__name'
        ).annotate(
            total_views=Sum('views_count')
        ).order_by('-total_views').first()
        
        stats = {
            'total_products': total_products,
            'active_products': active_products,
            'out_of_stock': out_of_stock,
            'sold_out': sold_out,
            'featured_products': featured_products,
            'new_products_today': new_products_today,
            'total_sales': total_sales,
            'total_revenue': float(total_revenue),
            'average_price': float(average_price),
            'most_viewed_category': {
                'category': most_viewed_category['category__name'] if most_viewed_category else 'Aucune',
                'views': most_viewed_category['total_views'] if most_viewed_category else 0
            }
        }
        
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Erreur statistiques produits: {str(e)}")
        return Response(
            {'error': 'Erreur lors du calcul des statistiques'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_bulk_update_products(request):
    """Mise à jour en masse des produits"""
    try:
        product_ids = request.data.get('product_ids', [])
        update_data = request.data.copy()
        update_data.pop('product_ids', None)
        
        if not product_ids:
            return Response(
                {'error': 'Aucun produit sélectionné'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mise à jour sécurisée
        products = Listing.objects.filter(id__in=product_ids)
        
        # Empêcher la modification des champs sensibles
        restricted_fields = ['user', 'created_at']
        for field in restricted_fields:
            if field in update_data:
                return Response(
                    {'error': f'Vous ne pouvez pas modifier {field}'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Mettre à jour les produits
        updated_count = products.update(**update_data)
        
        return Response({
            'message': f'{updated_count} produit(s) mis à jour',
            'count': updated_count
        })
        
    except Exception as e:
        logger.error(f"Erreur mise à jour en masse: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_bulk_delete_products(request):
    """Suppression en masse des produits"""
    try:
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response(
                {'error': 'Aucun produit sélectionné'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        products = Listing.objects.filter(id__in=product_ids)
        deleted_count = products.count()
        
        # Supprimer les produits
        products.delete()
        
        return Response({
            'message': f'{deleted_count} produit(s) supprimé(s)',
            'count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Erreur suppression en masse: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    
