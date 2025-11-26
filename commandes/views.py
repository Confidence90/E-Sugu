from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer
from paniers.models import Panier  # ton modèle de panier renommé
from listings.models import Listing
from decimal import Decimal 
from transactions.models import Transaction 
from notifications.models import Notification  # Import the Notification model
import csv
from datetime import datetime
from django.utils import timezone
from django.http import HttpResponse  # Ajouter cet import
from django.db import models

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


class OrderStatsView(APIView):
        permission_classes = [permissions.IsAuthenticated]

        def get(self, request):
            user = request.user
            orders = Order.objects.filter(user=user)
            
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
            
            return Response({
                'total_orders': orders.count(),
                'status_stats': status_stats,
                'total_revenue': float(total_revenue),
                'monthly_orders': monthly_orders
            })