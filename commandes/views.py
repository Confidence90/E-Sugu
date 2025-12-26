from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer
from paniers.models import Panier  # ton modèle de panier renommé
from listings.models import Listing
from decimal import Decimal 
#from transactions.models import Transaction 
from payments.models import Transaction  # Import the Transaction model
from notifications.models import Notification  # Import the Notification model
import csv
from rest_framework.decorators import api_view, permission_classes, action
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.http import HttpResponse  # Ajouter cet import
from django.db import models
from datetime import timedelta
from users.models import User
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, DurationField, Q
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek, TruncDay

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        
        # Filtrage par statut
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtrage par pays
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(shipping_country__icontains=country)
        
        # Filtrage par date
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Recherche par numéro de commande
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(order_number__icontains=search)
        
        return queryset

class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            panier_items = Panier.objects.filter(user=user)

            try:
                panier = Panier.objects.get(user=user)
            except Panier.DoesNotExist:
                return Response({'error': 'Panier non trouvé'}, status=status.HTTP_400_BAD_REQUEST)

            # 🔥 Validation du panier avant création de commande
            can_create, validation_message = panier.can_create_order()
            if not can_create:
                return Response({'error': validation_message}, status=status.HTTP_400_BAD_REQUEST)
            
            if not panier_items.exists():
                return Response({'error': 'Votre panier est vide.'}, status=status.HTTP_400_BAD_REQUEST)
            
            from django.db import transaction  # Ensure transaction is imported

            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    shipping_country=request.data.get('shipping_country', ''),
                    shipping_method=request.data.get('shipping_method', ''),
                    total_price=0  # sera mis à jour plus tard
                )
                total = Decimal('0.00')

                for panier_item in panier.items.all():
                    listing = panier_item.listing
                    price = listing.price
                    quantity = panier_item.quantity
                    OrderItem.objects.create(
                        order=order,
                        listing=listing,
                        quantity=quantity,
                        price=price,
                    )
                    if not listing.mark_as_sold(quantity):
                        raise Exception(f"Stock insuffisant pour {listing.title}")
                    
                    # 🔥 NOTIFICATION au vendeur
                    Notification.objects.create(
                        user=listing.user,
                        type='order',
                        content=f'Nouvelle commande pour "{listing.title}" - Quantité: {quantity} - Commande #{order.order_number}'
                    )
                    
                    # Vérifier si le stock est épuisé après cette commande
                    if listing.is_out_of_stock:
                        Notification.objects.create(
                            user=listing.user,
                            type='listing',
                            content=f'Votre produit "{listing.title}" est maintenant épuisé.'
                        )
                    
                    total += price * quantity
                
                order.total_price = total
                order.save()

                payment_method = request.data.get('payment_method', 'momo')
                transaction_obj = Transaction.objects.create(
                    order=order,
                    buyer=user,
                    amount=total,
                    paymenet_method=payment_method,
                    status='pending'
                )
                
                # Calculer le net amount (exemple: 5% de commission)
                commission = total * Decimal('0.05')
                transaction_obj.commission = commission
                transaction_obj.net_amount = total - commission
                transaction_obj.save()

                panier_items.all().delete()  # vider le panier après commande
                serializer = OrderSerializer(order)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': f'Erreur lors de la création de la commande:{str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        """
        Prévisualiser la commande à partir du panier
        """
        user = request.user
        
        try:
            panier = Panier.objects.get(user=user)
        except Panier.DoesNotExist:
            return Response({'error': 'Panier non trouvé'}, status=status.HTTP_400_BAD_REQUEST)

        if not panier.items.exists():
            return Response({'error': 'Votre panier est vide'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculer le total et préparer les données de prévisualisation
        items_preview = []
        total = Decimal('0.00')
        
        for panier_item in panier.items.all():
            item_total = panier_item.listing.price * panier_item.quantity
            total += item_total
            
            items_preview.append({
                'listing_title': panier_item.listing.title,
                'quantity': panier_item.quantity,
                'unit_price': float(panier_item.listing.price),
                'item_total': float(item_total),
                'is_available': panier_item.is_available(),
                'available_quantity': panier_item.listing.available_quantity
            })

        can_create, validation_message = panier.can_create_order()

        return Response({
            'can_create_order': can_create,
            'validation_message': validation_message,
            'total_price': float(total),
            'item_count': panier.items.count(),
            'items_preview': items_preview,
            'shipping_country': request.data.get('shipping_country', ''),
            'shipping_method': request.data.get('shipping_method', '')
        })
# Nouvelle view pour les actions groupées
class BulkOrderActionView(APIView):
    def post(self, request):
        order_ids = request.data.get('order_ids', [])
        action = request.data.get('action')
        
        orders = Order.objects.filter(id__in=order_ids, user=request.user)
        
        if action == 'mark_packaged':
            orders.update(is_packaged=True)
        elif action == 'update_status':
            new_status = request.data.get('status')
            orders.update(status=new_status)
        
        return Response({'updated': orders.count()})
class ExportOrdersView(APIView):
        permission_classes = [permissions.IsAuthenticated]

        def get(self, request):
            # Récupérer les paramètres de filtrage
            status = request.GET.get('status')
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            
            # Filtrer les commandes
            orders = Order.objects.filter(user=request.user)
            if status:
                orders = orders.filter(status=status)
            if date_from:
                orders = orders.filter(created_at__gte=date_from)
            if date_to:
                orders = orders.filter(created_at__lte=date_to)
            
            # Créer la réponse CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="commandes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Numéro de commande', 'Date', 'Statut', 'Prix total', 
                'Méthode de paiement', 'Pays', 'Méthode d\'expédition'
            ])
            
            for order in orders:
                writer.writerow([
                    order.order_number,
                    order.created_at.strftime('%Y-%m-%d %H:%M'),
                    order.get_status_display(),
                    order.total_price,
                    order.payment_method() or '',
                    order.shipping_country,
                    order.shipping_method
                ])
            
            return response


# commandes/views.py - MODIFIER OrderStatsView

class OrderStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Vérifier si l'utilisateur est admin
        is_admin = user.is_staff or user.is_superuser or user.role == 'admin'
        
        if is_admin:
            # 🔥 Admin : voir toutes les commandes
            orders = Order.objects.all()
            stats_type = 'admin'
        else:
            # 🔥 Utilisateur normal : voir seulement ses commandes
            orders = Order.objects.filter(user=user)
            stats_type = 'user'
        
        # Statistiques par statut
        status_stats = {}
        for status_code, status_name in Order.STATUS_CHOICES:
            count = orders.filter(status=status_code).count()
            status_stats[status_name] = count
        
        # Chiffre d'affaires total
        total_revenue = orders.aggregate(total=models.Sum('total_price'))['total'] or 0
        
        # Commandes du mois
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_orders = orders.filter(
            created_at__month=current_month,
            created_at__year=current_year
        ).count()
        
        # Préparer la réponse
        response_data = {
            'stats_type': stats_type,
            'total_orders': orders.count(),
            'status_stats': status_stats,
            'total_revenue': float(total_revenue),
            'monthly_orders': monthly_orders,
        }
        
        # Ajouter des statistiques supplémentaires pour l'admin
        if is_admin:
            
            seven_days_ago = timezone.now() - timedelta(days=7)
            
            # Commandes récentes
            recent_orders = orders.filter(
                created_at__gte=seven_days_ago
            ).count()
            
            # Revenue récent
            recent_revenue = orders.filter(
                created_at__gte=seven_days_ago
            ).aggregate(total=Sum('total_price'))['total'] or 0
            
            # Top vendeurs
            
            top_vendors = Order.objects.values(
                'listing__user__email'
            ).annotate(
                order_count=Count('id'),
                total_revenue=Sum('total_price')
            ).order_by('-total_revenue')[:5]
            
            response_data['admin_stats'] = {
                'recent_orders': recent_orders,
                'recent_revenue': float(recent_revenue),
                'average_order_value': float(total_revenue / orders.count()) if orders.count() > 0 else 0,
                'top_vendors': list(top_vendors),
            }
        
        return Response(response_data)
    
# Ajoutez ces classes AVANT ou APRÈS OrderStatsView dans views.py

class AdminOrderStatsView(APIView):
    """Statistiques des commandes pour les administrateurs seulement"""
    permission_classes = [permissions.IsAdminUser]  # 🔥 Admin seulement

    def get(self, request):
        # Récupérer TOUTES les commandes (pas de filtre par user)
        orders = Order.objects.all()
        
        # Statistiques par statut
        status_stats = {}
        for status_code, status_name in Order.STATUS_CHOICES:
            count = orders.filter(status=status_code).count()
            status_stats[status_name] = count
        
        # Chiffre d'affaires total
        total_revenue = orders.aggregate(total=models.Sum('total_price'))['total'] or 0
        
        # Commandes du mois
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_orders = orders.filter(
            created_at__month=current_month,
            created_at__year=current_year
        ).count()
        
        # 🔥 Statistiques supplémentaires pour admin
        # Commandes par vendeur
       
        vendor_stats = Order.objects.values(
            'listing__user__email', 
            'listing__user__first_name',
            'listing__user__last_name'
        ).annotate(
            order_count=models.Count('id'),
            total_revenue=models.Sum('total_price')
        ).order_by('-total_revenue')[:10]
        
        # Commandes par période (7 derniers jours)
        from datetime import timedelta
        seven_days_ago = timezone.now() - timedelta(days=7)
        orders_last_7_days = orders.filter(
            created_at__gte=seven_days_ago
        ).count()
        
        revenue_last_7_days = orders.filter(
            created_at__gte=seven_days_ago
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        return Response({
            'total_orders': orders.count(),
            'status_stats': status_stats,
            'total_revenue': float(total_revenue),
            'monthly_orders': monthly_orders,
            
            # 🔥 Statistiques admin supplémentaires
            'admin_stats': {
                'orders_last_7_days': orders_last_7_days,
                'revenue_last_7_days': float(revenue_last_7_days),
                'average_order_value': float(total_revenue / orders.count()) if orders.count() > 0 else 0,
                'top_vendors': list(vendor_stats),
                'pending_orders': orders.filter(status='pending').count(),
                'completed_orders': orders.filter(status='completed').count(),
                'cancelled_orders': orders.filter(status='cancelled').count(),
            }
        })


class UserOrderStatsView(APIView):
    """Statistiques des commandes pour les utilisateurs normaux seulement"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user)  # 🔥 Seulement ses commandes
        
        # Statistiques par statut
        status_stats = {}
        for status_code, status_name in Order.STATUS_CHOICES:
            count = orders.filter(status=status_code).count()
            status_stats[status_name] = count
        
        # Chiffre d'affaires total (ses achats)
        total_revenue = orders.aggregate(total=models.Sum('total_price'))['total'] or 0
        
        # Commandes du mois
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_orders = orders.filter(
            created_at__month=current_month,
            created_at__year=current_year
        ).count()
        
        # Statistiques spécifiques acheteur
        if user.is_seller or hasattr(user, 'vendor_profile'):
            # Si c'est aussi un vendeur, ajouter ses ventes
            vendor_orders = Order.objects.filter(listing__user=user)
            vendor_revenue = vendor_orders.aggregate(total=Sum('total_price'))['total'] or 0
            
            return Response({
                'user_type': 'seller',
                'total_orders_as_buyer': orders.count(),
                'total_orders_as_seller': vendor_orders.count(),
                'status_stats_as_buyer': status_stats,
                'total_spent': float(total_revenue),
                'total_earned': float(vendor_revenue),
                'monthly_orders': monthly_orders,
                'monthly_sales': vendor_orders.filter(
                    created_at__month=current_month,
                    created_at__year=current_year
                ).count(),
            })
        
        return Response({
            'user_type': 'buyer',
            'total_orders': orders.count(),
            'status_stats': status_stats,
            'total_revenue': float(total_revenue),
            'monthly_orders': monthly_orders,
        })
# commandes/views.py - AJOUTER ces endpoints

class AdminDashboardStatsView(APIView):
    """Statistiques complètes pour le dashboard admin"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        
        
        orders = Order.objects.all()
        today = timezone.now()
        
        # Statistiques de base
        total_orders = orders.count()
        total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0
        
        # Statistiques par période
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)
        
        orders_last_7_days = orders.filter(created_at__gte=last_7_days).count()
        revenue_last_7_days = orders.filter(
            created_at__gte=last_7_days
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Distribution par statut
        status_distribution = {}
        for status_code, status_name in Order.STATUS_CHOICES:
            count = orders.filter(status=status_code).count()
            status_distribution[status_name] = count
        
        # Tendances quotidiennes (7 derniers jours)
        daily_trends = []
        for i in range(7):
            date = today - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_orders = orders.filter(created_at__range=[day_start, day_end])
            daily_trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'orders': day_orders.count(),
                'revenue': float(day_orders.aggregate(total=Sum('total_price'))['total'] or 0)
            })
        
        # Top vendeurs
        top_vendors = Order.objects.values(
            'listing__user__email',
            'listing__user__first_name',
            'listing__user__last_name'
        ).annotate(
            total_orders=Count('id'),
            total_revenue=Sum('total_price'),
            avg_order_value=Avg('total_price')
        ).order_by('-total_revenue')[:10]
        
        # Top produits
        top_products = Order.objects.values(
            'listing__title',
            'listing__category__name'
        ).annotate(
            times_ordered=Count('id'),
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_revenue')[:10]
        
        # Métriques de performance
        avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0
        
        # Convertissez les QuerySets en listes
        top_vendors_list = []
        for vendor in top_vendors:
            top_vendors_list.append({
                'email': vendor['listing__user__email'],
                'name': f"{vendor['listing__user__first_name'] or ''} {vendor['listing__user__last_name'] or ''}".strip(),
                'total_orders': vendor['total_orders'],
                'total_revenue': float(vendor['total_revenue'] or 0),
                'avg_order_value': float(vendor['avg_order_value'] or 0)
            })
        
        top_products_list = []
        for product in top_products:
            top_products_list.append({
                'title': product['listing__title'],
                'category': product['listing__category__name'],
                'times_ordered': product['times_ordered'],
                'total_quantity': product['total_quantity'],
                'total_revenue': float(product['total_revenue'] or 0)
            })
        
        return Response({
            'overview': {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'orders_last_7_days': orders_last_7_days,
                'revenue_last_7_days': float(revenue_last_7_days),
                'avg_order_value': avg_order_value,
            },
            'status_distribution': status_distribution,
            'daily_trends': daily_trends[::-1],  # Inverser pour avoir du plus ancien au plus récent
            'top_vendors': top_vendors_list,
            'top_products': top_products_list,
            'period': {
                'start_date': last_30_days.strftime('%Y-%m-%d'),
                'end_date': today.strftime('%Y-%m-%d')
            }
        })


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_orders_analytics(request):
   
    
    # Commandes par mois
    monthly_stats = Order.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        orders=Count('id'),
        revenue=Sum('total_price'),
        avg_order_value=Avg('total_price')
    ).order_by('month')
    
    # Commandes par semaine
    weekly_stats = Order.objects.annotate(
        week=TruncWeek('created_at')
    ).values('week').annotate(
        orders=Count('id'),
        revenue=Sum('total_price')
    ).order_by('-week')[:12]
    
    # Conversion des QuerySets
    monthly_data = []
    for stat in monthly_stats:
        monthly_data.append({
            'month': stat['month'].strftime('%Y-%m'),
            'orders': stat['orders'],
            'revenue': float(stat['revenue'] or 0),
            'avg_order_value': float(stat['avg_order_value'] or 0)
        })
    
    weekly_data = []
    for stat in weekly_stats:
        weekly_data.append({
            'week': stat['week'].strftime('%Y-%m-%d'),
            'orders': stat['orders'],
            'revenue': float(stat['revenue'] or 0)
        })
    
    return Response({
        'monthly_analytics': monthly_data,
        'weekly_analytics': weekly_data,
    })

# commandes/views.py - AJOUTER
class VendorOrdersView(APIView):
    """Vue pour que les vendeurs voient leurs commandes"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Récupérer toutes les commandes du vendeur"""
        user = request.user
        
        # Vérifier que l'utilisateur est un vendeur
        if not (user.is_seller or hasattr(user, 'vendor_profile')):
            return Response(
                {'error': 'Accès réservé aux vendeurs'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Récupérer les commandes via les transactions
        vendor_transactions = Transaction.objects.filter(
            seller=user,
            status='completed'
        ).select_related('order', 'listing', 'buyer').exclude(order__isnull=True)
        
        # Si vous voulez récupérer directement via OrderItem
        from django.db.models import Q
        vendor_orders = Order.objects.filter(
            Q(items__listing__user=user) |  # Commandes de ses produits
            Q(transactions__seller=user)     # Commandes via transactions
        ).distinct().select_related('user').prefetch_related('items')
         # Si aucune transaction, vérifier via OrderItem
        if not vendor_transactions.exists():
            from django.db.models import Q
            
            # Essayer via OrderItem
            vendor_orders = Order.objects.filter(
                Q(items__listing__user=user)  # Commandes avec des items du vendeur
            ).distinct().select_related('user').prefetch_related('items')
        else:
            # Récupérer les commandes depuis les transactions
            order_ids = vendor_transactions.values_list('order_id', flat=True).distinct()
            vendor_orders = Order.objects.filter(id__in=order_ids).select_related('user').prefetch_related('items')
        
        # Préparer les données de réponse
        orders_data = []
        for order in vendor_orders:
            vendor_items = []
            for item in order.items.all():
                if item.listing and item.listing.user == user:  # Seulement les items du vendeur
                    vendor_items.append({
                        'id': item.id,
                        'listing_id': item.listing.id,
                        'listing_title': item.listing.title,
                        'quantity': item.quantity,
                        'price': float(item.price),
                        'subtotal': float(item.subtotal())
                    })
            
            if vendor_items:  # Seulement les commandes avec ses produits
                orders_data.append({
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'buyer': {
                        'id': order.user.id,
                        'name': f"{order.user.first_name} {order.user.last_name}".strip() or order.user.username,
                        'email': order.user.email,
                        'phone': order.user.phone
                    },
                    'items': vendor_items,
                    'total_price': float(order.total_price),
                    'status': order.status,
                    'created_at': order.created_at,
                    'is_packaged': order.is_packaged,
                    'shipping_info': {
                        'country': order.shipping_country,
                        'method': order.shipping_method
                    }
                })
        
        return Response({
            'count': len(orders_data),
            'orders': orders_data
        }, status=status.HTTP_200_OK)

class VendorOrderDetailView(APIView):
    """Détails d'une commande spécifique pour le vendeur"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            
            # Vérifier que le vendeur a des produits dans cette commande
            vendor_items = order.items.filter(listing__user=request.user)
            if not vendor_items.exists():
                return Response(
                    {'error': 'Commande non trouvée ou accès non autorisé'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Préparer les données détaillées
            order_data = {
                'order_id': order.id,
                'order_number': order.order_number,
                'buyer': {
                    'id': order.user.id,
                    'name': order.user.get_full_name(),
                    'email': order.user.email,
                    'phone': order.user.phone,
                    'location': order.user.location
                },
                'vendor_items': [],
                'other_items': [],
                'order_total': float(order.total_price),
                'vendor_total': 0.0,
                'status': order.status,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'shipping_info': {
                    'country': order.shipping_country,
                    'method': order.shipping_method
                },
                'payment_status': 'paid' if hasattr(order, 'transactions') and 
                order.transactions.filter(status='completed').exists() else 'pending'
            }
            
            # Séparer les items du vendeur des autres
            for item in order.items.all():
                item_data = {
                    'id': item.id,
                    'listing_title': item.listing.title,
                    'quantity': item.quantity,
                    'unit_price': float(item.price),
                    'subtotal': float(item.subtotal()),
                    'listing_status': item.listing.status
                }
                
                if item.listing.user == request.user:
                    order_data['vendor_items'].append(item_data)
                    order_data['vendor_total'] += float(item.subtotal())
                else:
                    order_data['other_items'].append(item_data)
            
            return Response(order_data, status=status.HTTP_200_OK)
            
        except Order.DoesNotExist:
            return Response(
                {'error': 'Commande non trouvée'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
# commandes/views.py - AJOUTER
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_orders_debug(request):
    """Endpoint de diagnostic pour les commandes vendeur"""
    user = request.user
    
    if not (user.is_seller or hasattr(user, 'vendor_profile')):
        return Response({'error': 'Accès réservé aux vendeurs'}, status=403)
    
    # Statistiques
    transactions_completed = Transaction.objects.filter(seller=user, status='completed').count()
    transactions_with_orders = Transaction.objects.filter(seller=user, status='completed', order__isnull=False).count()
    
    # Commandes via OrderItem
    orders_via_items = Order.objects.filter(items__listing__user=user).distinct().count()
    
    # Commandes via transactions
    orders_via_transactions = Order.objects.filter(
        transactions__seller=user,
        transactions__status='completed'
    ).distinct().count()
    
    # Toutes les commandes (union)
    all_orders = Order.objects.filter(
        Q(items__listing__user=user) |
        Q(transactions__seller=user, transactions__status='completed')
    ).distinct()
    
    debug_data = {
        'vendor_info': {
            'id': user.id,
            'email': user.email,
            'is_seller': user.is_seller,
            'has_vendor_profile': hasattr(user, 'vendor_profile'),
            'vendor_profile_id': user.vendor_profile.id if hasattr(user, 'vendor_profile') else None
        },
        'transactions_stats': {
            'total_completed': transactions_completed,
            'with_orders': transactions_with_orders,
            'without_orders': transactions_completed - transactions_with_orders
        },
        'orders_stats': {
            'via_order_items': orders_via_items,
            'via_transactions': orders_via_transactions,
            'total_unique': all_orders.count()
        },
        'sample_transactions': list(Transaction.objects.filter(
            seller=user, status='completed'
        ).values('id', 'listing__title', 'order_id', 'created_at')[:5]),
        'sample_orders': list(Order.objects.filter(
            Q(items__listing__user=user) |
            Q(transactions__seller=user, transactions__status='completed')
        ).distinct().values('id', 'order_number', 'status', 'created_at')[:5])
    }
    
    return Response(debug_data)

# commandes/views.py - AJOUTER OU MODIFIER

class BuyerOrdersViewSet(viewsets.ReadOnlyModelViewSet):
    """Commandes de l'utilisateur (acheteur)"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtrer les commandes où l'utilisateur est l'acheteur
        queryset = Order.objects.filter(user=self.request.user)
        # ... (filtres existants)
        return queryset


class SellerOrdersViewSet(viewsets.ReadOnlyModelViewSet):
    """Commandes des produits du vendeur"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Vérifier que c'est un vendeur
        if not (user.is_seller or hasattr(user, 'vendor_profile')):
            return Order.objects.none()
        
        # Filtrer les commandes qui contiennent ses produits
        queryset = Order.objects.filter(
            items__listing__user=user
        ).distinct()
        
        # Appliquer les mêmes filtres
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # ... autres filtres
        
        return queryset
    
# commandes/views.py - AJOUTER
class VendorOrderStatusUpdateView(APIView):
    """Mettre à jour le statut d'une commande pour le vendeur"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        try:
            user = request.user
            new_status = request.data.get('status')
            
            if not new_status:
                return Response(
                    {'error': 'Statut requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier que le vendeur a accès à cette commande
            order = Order.objects.filter(
                items__listing__user=user,
                id=order_id
            ).first()
            
            if not order:
                return Response(
                    {'error': 'Commande non trouvée ou accès non autorisé'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Mettre à jour le statut
            order.status = new_status
            order.save()
            
            # Créer une notification pour l'acheteur
            from notifications.models import Notification
            Notification.objects.create(
                user=order.user,
                type='order_update',
                content=f'Le statut de votre commande #{order.order_number} a été mis à jour: {new_status}'
            )
            
            return Response({
                'order_id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'updated_at': order.updated_at
            }, status=status.HTTP_200_OK)
            
        except Order.DoesNotExist:
            return Response(
                {'error': 'Commande non trouvée'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Erreur lors de la mise à jour: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
# Dans commandes/views.py - AJOUTER

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_time_series_stats(request):
    """Statistiques par période (jour, semaine, mois)"""

    
    # Paramètres
    period = request.GET.get('period', 'day')  # day, week, month
    days = int(request.GET.get('days', 30))
    
    # Sélectionner la fonction de troncation
    if period == 'week':
        trunc_func = TruncWeek
    elif period == 'month':
        trunc_func = TruncMonth
    else:
        trunc_func = TruncDay
    
    # Calculer la date de début
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Agréger par période
    time_series = Order.objects.filter(
        created_at__gte=start_date
    ).annotate(
        period=trunc_func('created_at')
    ).values('period').annotate(
        order_count=Count('id'),
        total_revenue=Sum('total_price'),
        avg_order_value=Avg('total_price'),
        unique_customers=Count('user', distinct=True)
    ).order_by('period')
    
    # Formater les données
    formatted_data = []
    for data in time_series:
        formatted_data.append({
            'period': data['period'].strftime('%Y-%m-%d'),
            'orders': data['order_count'],
            'revenue': float(data['total_revenue'] or 0),
            'avg_order_value': float(data['avg_order_value'] or 0),
            'unique_customers': data['unique_customers']
        })
    
    return Response({
        'period': period,
        'days': days,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'data': formatted_data
    })

# Dans commandes/views.py - AJOUTER

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_performance_metrics(request):
    """Métriques de performance avancées"""
    
    orders = Order.objects.all()
    total_orders = orders.count()
    
    # Taux de conversion (si vous avez des données de vues)
    from listings.models import ListingView
    total_listing_views = ListingView.objects.count()
    conversion_rate = (total_orders / total_listing_views * 100) if total_listing_views > 0 else 0
    
    # Temps moyen de traitement
    completed_orders = orders.filter(status='delivered')
    avg_processing_time = None
    if completed_orders.exists():
        total_days = 0
        for order in completed_orders:
            if order.created_at and hasattr(order, 'delivered_at') and order.delivered_at:
                processing_days = (order.delivered_at - order.created_at).days
                total_days += processing_days
        avg_processing_time = total_days / completed_orders.count() if completed_orders.count() > 0 else 0
    
    # Valeur à vie du client (CLV) - estimation simple
    from django.db.models import Count, Avg
    customer_stats = Order.objects.values('user').annotate(
        order_count=Count('id'),
        total_spent=Sum('total_price')
    ).aggregate(
        avg_orders_per_customer=Avg('order_count'),
        avg_spent_per_customer=Avg('total_spent')
    )
    
    # Taux de répétition
    repeat_customers = User.objects.annotate(
        order_count=Count('orders')
    ).filter(order_count__gt=1).count()
    
    total_customers = User.objects.filter(orders__isnull=False).distinct().count()
    repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
    
    return Response({
        'conversion_metrics': {
            'conversion_rate': round(conversion_rate, 2),
            'total_views': total_listing_views,
            'total_orders': total_orders,
        },
        'efficiency_metrics': {
            'avg_processing_time_days': round(avg_processing_time, 1) if avg_processing_time else None,
            'pending_orders': orders.filter(status='pending').count(),
            'processing_orders': orders.filter(status__in=['confirmed', 'ready_to_ship']).count(),
        },
        'customer_metrics': {
            'total_customers': total_customers,
            'repeat_customers': repeat_customers,
            'repeat_rate': round(repeat_rate, 2),
            'avg_orders_per_customer': round(customer_stats['avg_orders_per_customer'] or 0, 1),
            'avg_customer_lifetime_value': round(customer_stats['avg_spent_per_customer'] or 0, 2),
        }
    })

# Dans commandes/views.py - AJOUTER

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_geographic_analysis(request):
    """Analyse des commandes par région/pays"""
    
    # Commandes par pays
    orders_by_country = Order.objects.exclude(
        shipping_country__isnull=True
    ).exclude(
        shipping_country=''
    ).values('shipping_country').annotate(
        order_count=Count('id'),
        total_revenue=Sum('total_price'),
        avg_order_value=Avg('total_price')
    ).order_by('-total_revenue')
    
    # Top villes (si vous avez les données)
    from users.models import User
    customers_by_location = User.objects.filter(
        orders__isnull=False,
        location__isnull=False
    ).exclude(location='').values('location').annotate(
        customer_count=Count('id', distinct=True),
        order_count=Count('orders'),
        total_spent=Sum('orders__total_price')
    ).order_by('-total_spent')[:10]
    
    return Response({
        'by_country': [
            {
                'country': item['shipping_country'],
                'orders': item['order_count'],
                'revenue': float(item['total_revenue'] or 0),
                'avg_order_value': float(item['avg_order_value'] or 0)
            }
            for item in orders_by_country
        ],
        'by_location': [
            {
                'location': item['location'],
                'customers': item['customer_count'],
                'orders': item['order_count'],
                'total_spent': float(item['total_spent'] or 0)
            }
            for item in customers_by_location
        ]
    })

# Dans commandes/views.py - AJOUTER

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_product_analysis(request):
    """Analyse détaillée des produits"""
    
    from listings.models import Listing
    
    # Produits les plus vendus avec plus de détails
    top_products = Order.objects.values(
        'listing__id',
        'listing__title',
        'listing__category__name',
        'listing__price',
        'listing__user__email'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_orders=Count('id', distinct=True),
        total_revenue=Sum('total_price'),
        unique_customers=Count('user', distinct=True)
    ).order_by('-total_revenue')[:20]
    
    # Analyse des catégories
    category_analysis = Order.objects.values(
        'listing__category__name'
    ).annotate(
        product_count=Count('listing__id', distinct=True),
        order_count=Count('id'),
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price'),
        avg_order_value=Avg('total_price')
    ).order_by('-total_revenue')
    
    # ✅ CORRECTION : Utilisez les champs qui existent réellement
    # Taux d'épuisement des stocks - Utilisez 'quantity' et 'quantity_sold' au lieu de 'available_quantity'
    out_of_stock_products = Listing.objects.filter(
        status='out_of_stock'
    ).count()
    
    # Calculer les produits avec stock faible (moins de 20% du stock initial)
    # Nous devons le faire manuellement car pas de champ available_quantity
    all_listings = Listing.objects.all()
    low_stock_count = 0
    for listing in all_listings:
        # Calculer la quantité disponible
        available = listing.quantity - listing.quantity_sold if hasattr(listing, 'quantity') and hasattr(listing, 'quantity_sold') else 0
        
        # Si moins de 20% du stock initial reste
        if listing.quantity > 0 and available <= (listing.quantity * 0.2):
            low_stock_count += 1
    
    # Alternative plus simple : utiliser la logique existante du modèle
    low_stock_products = Listing.objects.filter(
        quantity__gt=0  # Si vous avez un stock
    ).annotate(
        remaining=models.F('quantity') - models.F('quantity_sold')
    ).filter(
        remaining__lte=3,
        remaining__gt=0
    ).count()
    
    # Calculer le pourcentage de santé des stocks
    total_products = Listing.objects.count()
    if total_products > 0:
        # Produits avec stock suffisant (plus de 3 unités restantes)
        healthy_stock_count = Listing.objects.annotate(
            remaining=models.F('quantity') - models.F('quantity_sold')
        ).filter(
            remaining__gt=3
        ).count()
        stock_health_percentage = round((healthy_stock_count / total_products) * 100, 2)
    else:
        stock_health_percentage = 0
    
    return Response({
        'top_products': [
            {
                'id': item['listing__id'],
                'title': item['listing__title'],
                'category': item['listing__category__name'],
                'price': float(item['listing__price'] or 0),
                'seller': item['listing__user__email'],
                'total_quantity_sold': item['total_quantity'],
                'total_orders': item['total_orders'],
                'total_revenue': float(item['total_revenue'] or 0),
                'unique_customers': item['unique_customers'],
                'conversion_rate': round((item['total_orders'] / item['unique_customers'] * 100), 2) if item['unique_customers'] > 0 else 0
            }
            for item in top_products
        ],
        'category_analysis': [
            {
                'category': item['listing__category__name'],
                'products': item['product_count'],
                'orders': item['order_count'],
                'quantity_sold': item['total_quantity'],
                'revenue': float(item['total_revenue'] or 0),
                'avg_order_value': float(item['avg_order_value'] or 0),
                'market_share': round((item['total_revenue'] or 0) / sum(cat['total_revenue'] or 0 for cat in category_analysis) * 100, 2) if sum(cat['total_revenue'] or 0 for cat in category_analysis) > 0 else 0
            }
            for item in category_analysis
        ],
        'inventory_health': {
            'out_of_stock': out_of_stock_products,
            'low_stock': low_stock_count,
            'total_products': total_products,
            'stock_health_percentage': stock_health_percentage,
            'using_fields': {
                'quantity_field': 'quantity' if hasattr(Listing(), 'quantity') else 'N/A',
                'quantity_sold_field': 'quantity_sold' if hasattr(Listing(), 'quantity_sold') else 'N/A',
                'available_calculation': 'quantity - quantity_sold'
            }
        }
    })

# Dans commandes/views.py - AJOUTER

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_alerts(request):
    """Alertes importantes pour l'admin"""
    
    from datetime import datetime, timedelta
    
    alerts = []
    
    # Commandes en attente depuis longtemps
    long_pending_orders = Order.objects.filter(
        status='pending',
        created_at__lte=timezone.now() - timedelta(hours=24)
    ).count()
    
    if long_pending_orders > 0:
        alerts.append({
            'type': 'warning',
            'title': 'Commandes en attente',
            'message': f'{long_pending_orders} commande(s) en attente depuis plus de 24h',
            'priority': 'high',
            'action_url': '/admin/commandes/order/?status=pending'
        })
    
    # Stocks épuisés
    from listings.models import Listing
    out_of_stock = Listing.objects.filter(status='out_of_stock').count()
    
    if out_of_stock > 0:
        alerts.append({
            'type': 'danger',
            'title': 'Stocks épuisés',
            'message': f'{out_of_stock} produit(s) épuisé(s)',
            'priority': 'medium',
            'action_url': '/admin/listings/listing/?status=out_of_stock'
        })
    
    # Avis négatifs récents
    from reviews.models import Review
    recent_negative_reviews = Review.objects.filter(
        rating__lte=2,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    if recent_negative_reviews > 0:
        alerts.append({
            'type': 'danger',
            'title': 'Avis négatifs',
            'message': f'{recent_negative_reviews} avis négatif(s) cette semaine',
            'priority': 'high',
            'action_url': '/admin/reviews/review/?rating__lte=2'
        })
    
    # Vendeurs inactifs
    from django.db.models import Count
    inactive_vendors = User.objects.filter(
        role='seller',
        listings__isnull=False
    ).annotate(
        recent_orders=Count('listings__orders', filter=Q(listings__orders__created_at__gte=timezone.now() - timedelta(days=30)))
    ).filter(recent_orders=0).count()
    
    if inactive_vendors > 0:
        alerts.append({
            'type': 'info',
            'title': 'Vendeurs inactifs',
            'message': f'{inactive_vendors} vendeur(s) sans vente depuis 30 jours',
            'priority': 'low',
            'action_url': '/admin/users/user/?role=seller'
        })
    
    return Response({
        'alerts': alerts,
        'total_alerts': len(alerts),
        'high_priority_alerts': len([a for a in alerts if a['priority'] == 'high']),
        'last_updated': timezone.now().isoformat()
    })

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_comprehensive_dashboard(request):
    """Dashboard complet avec toutes les métriques"""
    
    # Appeler toutes les fonctions et combiner les résultats
    from .views import (
        admin_time_series_stats,
        admin_performance_metrics,
        admin_geographic_analysis,
        admin_product_analysis,
        admin_alerts
    )
    
    # Simuler des appels (en production, vous extrairiez la logique)
    response = {
        'summary': {
            'total_orders': Order.objects.count(),
            'total_revenue': float(Order.objects.aggregate(total=Sum('total_price'))['total'] or 0),
            'total_customers': User.objects.filter(orders__isnull=False).distinct().count(),
            'total_sellers': User.objects.filter(role='seller').count(),
            'avg_order_value': float(Order.objects.aggregate(avg=Avg('total_price'))['avg'] or 0),
        },
        'time_period': {
            'today': timezone.now().strftime('%Y-%m-%d'),
            'last_30_days': (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        },
        'modules': {
            'sales_overview': True,
            'customer_analytics': True,
            'product_analysis': True,
            'geographic_insights': True,
            'alerts': True,
            'performance_metrics': True
        }
    }
    
    return Response(response)

# Ajoutez cette vue à votre views.py
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_all_orders(request):
    """Toutes les commandes pour l'admin avec pagination"""
    
    # Récupérer les paramètres
    status = request.GET.get('status')
    search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    ordering = request.GET.get('ordering', '-created_at')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    # Construire le queryset
    orders = Order.objects.all().select_related(
        'user', 
        'listing__user', 
        'listing__category'
    ).prefetch_related('items', 'transactions')
    
    # Appliquer les filtres
    if status and status != 'all':
        orders = orders.filter(status=status)
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(listing__title__icontains=search)
        )
    
    if date_from:
        orders = orders.filter(created_at__gte=date_from)
    
    if date_to:
        orders = orders.filter(created_at__lte=date_to)
    
    # Ordonner
    orders = orders.order_by(ordering)
    
    # Pagination
    total_count = orders.count()
    start = (page - 1) * page_size
    end = start + page_size
    paginated_orders = orders[start:end]
    
    # Préparer les données
    orders_data = []
    for order in paginated_orders:
        # Trouver la transaction associée
        transaction = None
        if hasattr(order, 'transactions') and order.transactions.exists():
            transaction_obj = order.transactions.first()
            transaction = {
                'id': transaction_obj.id,
                'status': transaction_obj.status,
                'payment_method': getattr(transaction_obj, 'payment_method', getattr(transaction_obj, 'paymenet_method', '')),
            }
        
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'buyer': {
                'id': order.user.id,
                'email': order.user.email,
                'first_name': order.user.first_name,
                'last_name': order.user.last_name,
                'phone': getattr(order.user, 'phone', '')
            },
            'listing': {
                'id': order.listing.id if order.listing else None,
                'title': order.listing.title if order.listing else 'Produit supprimé',
                'price': float(order.listing.price) if order.listing else 0,
                'user': {
                    'id': order.listing.user.id if order.listing else None,
                    'email': order.listing.user.email if order.listing else '',
                    'first_name': order.listing.user.first_name if order.listing else '',
                    'last_name': order.listing.user.last_name if order.listing else ''
                },
                'category': order.listing.category.name if order.listing and order.listing.category else None
            },
            'status': order.status,
            'total_price': float(order.total_price),
            'quantity': order.quantity,
            'shipping_country': order.shipping_country,
            'shipping_method': order.shipping_method,
            'is_packaged': order.is_packaged,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            'customer_notes': order.customer_notes,
            'shipping_address': order.shipping_address,
            'transaction': transaction
        })
    
    return Response({
        'count': total_count,
        'next': f'{request.build_absolute_uri(request.path)}?page={page + 1}' if end < total_count else None,
        'previous': f'{request.build_absolute_uri(request.path)}?page={page - 1}' if page > 1 else None,
        'results': orders_data
    })

# Dans commandes/views.py - AJOUTER
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_recent_orders(request):
    """
    Commandes récentes pour l'admin avec filtres avancés
    """
    
    # Paramètres de filtrage
    days = int(request.GET.get('days', 7))  # Par défaut 7 derniers jours
    status = request.GET.get('status')
    seller_email = request.GET.get('seller')
    buyer_email = request.GET.get('buyer')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    ordering = request.GET.get('ordering', '-created_at')
    
    # Date de début (X derniers jours)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Construire le queryset
    orders = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related(
        'user', 
        'listing__user', 
        'listing__category'
    ).prefetch_related(
        'items', 
        'transactions'
    )
    
    # Appliquer les filtres
    if status and status != 'all':
        orders = orders.filter(status=status)
    
    if seller_email:
        orders = orders.filter(listing__user__email__icontains=seller_email)
    
    if buyer_email:
        orders = orders.filter(user__email__icontains=buyer_email)
    
    if min_amount:
        orders = orders.filter(total_price__gte=min_amount)
    
    if max_amount:
        orders = orders.filter(total_price__lte=max_amount)
    
    if category:
        orders = orders.filter(listing__category__name__icontains=category)
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(listing__title__icontains=search) |
            Q(listing__description__icontains=search) |
            Q(shipping_country__icontains=search) |
            Q(shipping_method__icontains=search)
        )
    
    # Ordonner
    order_by_mapping = {
        'newest': '-created_at',
        'oldest': 'created_at',
        'price_high': '-total_price',
        'price_low': 'total_price',
        'quantity_high': '-quantity',
        'quantity_low': 'quantity'
    }
    
    order_field = order_by_mapping.get(ordering, ordering)
    orders = orders.order_by(order_field)
    
    # Statistiques avant pagination
    total_count = orders.count()
    total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0
    avg_order_value = orders.aggregate(avg=Avg('total_price'))['avg'] or 0
    
    # Distribution par statut
    status_distribution = orders.values('status').annotate(
        count=Count('id'),
        revenue=Sum('total_price')
    )
    
    # Top vendeurs récents
    top_vendors = orders.values(
        'listing__user__email',
        'listing__user__first_name',
        'listing__user__last_name'
    ).annotate(
        order_count=Count('id'),
        total_revenue=Sum('total_price'),
        avg_order_value=Avg('total_price')
    ).order_by('-total_revenue')[:5]
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated_orders = orders[start:end]
    
    # Préparer les données de réponse
    orders_data = []
    for order in paginated_orders:
        # Récupérer la transaction
        transaction = None
        if hasattr(order, 'transactions') and order.transactions.exists():
            t = order.transactions.first()
            transaction = {
                'id': t.id,
                'status': t.status,
                'payment_method': getattr(t, 'payment_method', getattr(t, 'paymenet_method', '')),
                'amount': float(t.amount) if t.amount else None,
                'created_at': t.created_at.isoformat() if t.created_at else None
            }
        
        # Récupérer tous les items
        items = []
        for item in order.items.all():
            items.append({
                'id': item.id,
                'listing_title': item.listing.title if item.listing else 'Produit supprimé',
                'quantity': item.quantity,
                'unit_price': float(item.price),
                'subtotal': float(item.subtotal()),
                'category': item.listing.category.name if item.listing and item.listing.category else None
            })
        
        # Calculer les jours depuis création
        days_since_creation = (timezone.now() - order.created_at).days if order.created_at else None
        
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'buyer': {
                'id': order.user.id,
                'email': order.user.email,
                'first_name': order.user.first_name,
                'last_name': order.user.last_name,
                'phone': getattr(order.user, 'phone', ''),
                'location': getattr(order.user, 'location', '')
            },
            'seller': {
                'id': order.listing.user.id if order.listing else None,
                'email': order.listing.user.email if order.listing else '',
                'first_name': order.listing.user.first_name if order.listing else '',
                'last_name': order.listing.user.last_name if order.listing else '',
                'phone': getattr(order.listing.user, 'phone', '') if order.listing else ''
            },
            'listing': {
                'id': order.listing.id if order.listing else None,
                'title': order.listing.title if order.listing else 'Produit supprimé',
                'price': float(order.listing.price) if order.listing else 0,
                'category': order.listing.category.name if order.listing and order.listing.category else None,
                'image_url': order.listing.get_first_image_url() if order.listing and hasattr(order.listing, 'get_first_image_url') else None
            },
            'status': order.status,
            'status_display': order.get_status_display(),
            'total_price': float(order.total_price),
            'quantity': order.quantity,
            'items': items,
            'shipping_info': {
                'country': order.shipping_country,
                'method': order.shipping_method,
                'address': order.shipping_address
            },
            'is_packaged': order.is_packaged,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            'customer_notes': order.customer_notes,
            'days_since_creation': days_since_creation,
            'requires_attention': (
                order.status == 'pending' and 
                order.created_at and 
                (timezone.now() - order.created_at).days >= 2
            ) if order.created_at else False,
            'transaction': transaction,
            'actions': {
                'can_update_status': True,
                'can_mark_packaged': not order.is_packaged and order.status in ['confirmed', 'ready_to_ship'],
                'can_cancel': order.status in ['pending', 'confirmed']
            }
        })
    
    # Préparer les métriques
    metrics = {
        'total_orders': total_count,
        'total_revenue': float(total_revenue),
        'avg_order_value': float(avg_order_value),
        'time_period': {
            'days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        },
        'status_distribution': {
            item['status']: {
                'count': item['count'],
                'revenue': float(item['revenue']) if item['revenue'] else 0
            }
            for item in status_distribution
        },
        'top_vendors': [
            {
                'email': vendor['listing__user__email'],
                'name': f"{vendor['listing__user__first_name'] or ''} {vendor['listing__user__last_name'] or ''}".strip(),
                'order_count': vendor['order_count'],
                'total_revenue': float(vendor['total_revenue'] or 0),
                'avg_order_value': float(vendor['avg_order_value'] or 0)
            }
            for vendor in top_vendors
        ]
    }
    
    # Lien pour la page suivante
    next_url = None
    if end < total_count:
        next_url = request.build_absolute_uri(
            f'{request.path}?page={page + 1}&page_size={page_size}'
        )
    
    previous_url = None
    if page > 1:
        previous_url = request.build_absolute_uri(
            f'{request.path}?page={page - 1}&page_size={page_size}'
        )
    
    return Response({
        'metadata': metrics,
        'pagination': {
            'count': total_count,
            'next': next_url,
            'previous': previous_url,
            'current_page': page,
            'total_pages': (total_count + page_size - 1) // page_size,
            'page_size': page_size
        },
        'filters_applied': {
            'days': days,
            'status': status,
            'seller': seller_email,
            'buyer': buyer_email,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'category': category,
            'search': search,
            'ordering': ordering
        },
        'orders': orders_data
    })


# Version simplifiée pour le dashboard
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_dashboard_recent_orders(request):
    """
    Commandes récentes simplifiées pour le dashboard
    """
    limit = int(request.GET.get('limit', 10))
    days = int(request.GET.get('days', 7))
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    orders = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    ).select_related(
        'user', 
        'listing__user'
    ).order_by('-created_at')[:limit]
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'buyer': {
                'email': order.user.email,
                'name': f"{order.user.first_name or ''} {order.user.last_name or ''}".strip()
            },
            'listing_title': order.listing.title if order.listing else 'Produit supprimé',
            'total_price': float(order.total_price),
            'quantity': order.quantity,
            'status': order.status,
            'status_display': order.get_status_display(),
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'requires_attention': (
                order.status == 'pending' and 
                order.created_at and 
                (timezone.now() - order.created_at).days >= 2
            ) if order.created_at else False,
            'is_packaged': order.is_packaged,
            'days_ago': (timezone.now() - order.created_at).days if order.created_at else None
        })
    
    return Response({
        'period': {
            'days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        },
        'total_recent_orders': Order.objects.filter(
            created_at__gte=start_date
        ).count(),
        'recent_orders': orders_data
    })


# Commandes nécessitant une attention urgente
@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def admin_urgent_orders(request):
    """
    Commandes nécessitant une attention urgente
    """
    # Commandes en attente depuis plus de 2 jours
    urgent_cutoff = timezone.now() - timedelta(days=2)
    
    urgent_orders = Order.objects.filter(
        Q(status='pending', created_at__lte=urgent_cutoff) |
        Q(status='confirmed', is_packaged=False, created_at__lte=timezone.now() - timedelta(days=1))
    ).select_related('user', 'listing__user').order_by('created_at')
    
    orders_data = []
    for order in urgent_orders:
        urgency_level = 'high' if order.status == 'pending' and order.created_at <= urgent_cutoff else 'medium'
        
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'buyer_email': order.user.email,
            'listing_title': order.listing.title if order.listing else 'Produit supprimé',
            'status': order.status,
            'total_price': float(order.total_price),
            'created_at': order.created_at.isoformat(),
            'days_pending': (timezone.now() - order.created_at).days,
            'urgency_level': urgency_level,
            'issue': 'pending_too_long' if order.status == 'pending' else 'not_packaged',
            'required_action': 'Approuver la commande' if order.status == 'pending' else 'Emballer la commande'
        })
    
    # Statistiques
    pending_old = Order.objects.filter(
        status='pending', 
        created_at__lte=urgent_cutoff
    ).count()
    
    confirmed_not_packaged = Order.objects.filter(
        status='confirmed', 
        is_packaged=False, 
        created_at__lte=timezone.now() - timedelta(days=1)
    ).count()
    
    return Response({
        'total_urgent': len(orders_data),
        'breakdown': {
            'pending_old': pending_old,
            'confirmed_not_packaged': confirmed_not_packaged
        },
        'urgent_orders': orders_data,
        'last_checked': timezone.now().isoformat()
    })