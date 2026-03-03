# payments/views.py
import stripe
import logging
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import Transaction
from listings.models import Listing
from django.db import transaction as db_transaction
from paniers.models import Panier, PanierItem  # Import des modèles panier
from .serializers import TransactionSerializer, CreateTransactionSerializer, PaymentConfirmationSerializer
from .services.stripe_service import StripeService
from commandes.models import Order, OrderItem
logger = logging.getLogger(__name__)
from django.utils import timezone

class TransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("=" * 50)
        print("🚀 NOUVELLE REQUÊTE PAYMENT RECEIVED")
        print("📥 Données reçues:", request.data)
        print("👤 Utilisateur:", request.user.id)
        print("🔑 Auth header:", request.headers.get('Authorization')[:50] + "..." if request.headers.get('Authorization') else 'None')
            # Vérifier l'état du panier immédiatement
        try:
            panier = Panier.objects.get(user=request.user)
            panier_count = panier.items.count()
            print(f"🛒 État du panier: {panier_count} articles")
            if panier_count == 0:
                print("❌ ❌ ❌ PANIER VIDE DÈS LE DÉBUT - ARRÊT IMMÉDIAT")
                return Response(
                    {'error': 'Le panier est vide. Ajoutez des articles avant de payer.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Panier.DoesNotExist:
            print("❌ PANIER DOES NOT EXIST")
            return Response(
                {'error': 'Panier non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        print("=" * 50)
        serializer = CreateTransactionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            listing_id = serializer.validated_data.get('listing_id')
            payment_method = serializer.validated_data['payment_method']
            
            try:
                # =============================================
                # GESTION DU PANIER COMPLET
                # =============================================
                if not listing_id:
                    # Paiement du panier complet
                    return self.process_panier_payment(request, payment_method)
                else:
                    # Paiement d'un seul article (comportement existant)
                    return self.process_single_payment(request, listing_id, payment_method)
                    
            except Exception as e:
                logger.error(f"❌ Erreur générale: {e}", exc_info=True)
                return Response(
                    {'error': 'Erreur lors du traitement de la demande'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Erreurs de sérialisation
        logger.warning(f"⚠️ Données invalides: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def process_panier_payment(self, request, payment_method):
        try:
            panier = Panier.objects.get(user=request.user)
            panier_items = panier.items.all().select_related('listing')

            if not panier_items.exists():
                return Response({'error': 'Panier vide'}, status=400)

            if not request.user.phone:
                return Response({'error': 'Numéro requis'}, status=400)

            # ==============================
            # Création Order
            # ==============================
            shipping_data = request.data.get('shipping_address', {})
            shipping_method_data = request.data.get('shipping_method', {})

            order = Order.objects.create(
                user=request.user,
                status='pending',
                shipping_address=shipping_data.get('address', ''),
                shipping_method=shipping_method_data.get('name', ''),
                total_price=panier.total_price(),
                order_number=f"ORD-{timezone.now().strftime('%y%m%d%H%M%S')}-{request.user.id}"
            )

            # ==============================
            # Création OrderItems
            # ==============================
            for item in panier_items:
                OrderItem.objects.create(
                    order=order,
                    listing=item.listing,
                    quantity=item.quantity,
                    price=item.listing.price
                )

            order.update_total()

            total_amount = float(order.total_price)

            # Validation Stripe
            StripeService.validate_amount(total_amount, 'xof')

            phone_full = f"{request.user.country_code}{request.user.phone}"

            payment_intent = StripeService.create_payment_intent_for_mobile(
                amount=total_amount,
                phone=phone_full,
                payment_method=payment_method
            )

            # Ajouter metadata Stripe
            stripe.PaymentIntent.modify(
                payment_intent.id,
                metadata={
                    'order_id': str(order.id),
                    'user_id': str(request.user.id),
                }
            )

            # ==============================
            # Création Transactions (avec commission)
            # ==============================
            with db_transaction.atomic():
                transactions = []
                total_commission = Decimal('0.00')
                total_net_amount = Decimal('0.00')

                for item in panier_items:
                    item_total = item.quantity * item.listing.price
                    commission = item_total * Decimal('0.07')
                    net_amount = item_total - commission

                    transaction = Transaction.objects.create(
                        listing=item.listing,
                        user=request.user,
                        seller=item.listing.user,
                        quantity=item.quantity,
                        amount=item.listing.price,
                        total_amount=item_total,
                        commission=commission,
                        net_amount=net_amount,
                        status='pending',
                        payment_method=payment_method,
                        stripe_payment_intent_id=payment_intent.id,
                        order=order
                    )

                    transactions.append(transaction)
                    total_commission += commission
                    total_net_amount += net_amount

            return Response({
                'status': 'requires_payment_method',
                'transaction_ids': [t.id for t in transactions],
                'payment_intent_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'total_amount': total_amount,
                'order_id': order.id,
                'total_commission': float(total_commission),
                'total_net_amount': float(total_net_amount),
                'currency': 'xof'
            }, status=201)

        except Exception as e:
            logger.error(f"Erreur paiement panier: {e}", exc_info=True)
            return Response({'error': 'Erreur interne'}, status=500)
        # Duplicate definition removed: process_panier_payment

    def get(self, request):
        """
        Récupérer les transactions de l'utilisateur
        """
        try:
            transactions = Transaction.objects.filter(user=request.user) | Transaction.objects.filter(seller=request.user)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"❌ Erreur récupération transactions: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération des transactions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class PaymentConfirmationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"🔍 Confirmation paiement - User: {request.user.id}, Data: {request.data}")
        serializer = PaymentConfirmationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_intent_id = serializer.validated_data['payment_intent_id']

        try:
            # 🔥 Récupérer les transactions en attente
            transactions = Transaction.objects.filter(
                stripe_payment_intent_id=payment_intent_id,
                user=request.user,
                status='pending'
            ).select_related('order')

            logger.info(f"📊 Transactions en attente trouvées: {transactions.count()}")

            if not transactions.exists():
                logger.warning(f"⚠️ Aucune transaction en attente trouvée pour {payment_intent_id}")
                return Response(
                    {'error': 'Aucune transaction en attente trouvée'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 🔥 Vérifier l'état Stripe
            payment_intent = StripeService.retrieve_payment_intent(payment_intent_id)

            if payment_intent.status != 'succeeded':
                return Response({
                    'status': payment_intent.status,
                    'message': f"Paiement en statut: {payment_intent.status}"
                }, status=status.HTTP_200_OK)

            # 🔥 TRAITEMENT ATOMIQUE AVEC VIDAGE DU PANIER
            with db_transaction.atomic():
                orders_updated = []
                # 1️⃣ Mettre à jour les transactions
                for transaction in transactions:
                    transaction.status = 'held'  # ou 'completed' selon votre logique
                    transaction.held_at = timezone.now()
                    transaction.save()
                    
                    # Marquer le listing comme vendu
                    transaction.listing.mark_as_sold(transaction.quantity)
                    if transaction.order:
                        order = transaction.order
                        if order.status == 'pending':
                            order.status = 'confirmed'
                            order.save()
                            orders_updated.append(order.id)
                            
                            # Notification au vendeur
                            from notifications.models import Notification
                            Notification.objects.create(
                                user=transaction.seller,
                                type='order_confirmed',
                                content=f'Commande #{order.order_number} confirmée (paiement reçu)'
                            )
                # 2️⃣ 🔥 VIDER LE PANIER ICI - DANS LA MÊME TRANSACTION
                try:
                    panier = Panier.objects.get(user=request.user)
                    items_removed = panier.items.count()
                    
                    if items_removed > 0:
                        panier.items.all().delete()
                        logger.info(f"✅ Panier vidé immédiatement: {items_removed} articles supprimés")
                        
                        # Vérification
                        if panier.items.count() == 0:
                            panier_vide = True
                        else:
                            logger.error(f"❌ Le panier n'a pas pu être vidé complètement")
                            panier_vide = False
                    else:
                        logger.info("ℹ️ Panier déjà vide")
                        panier_vide = True
                        
                except Panier.DoesNotExist:
                    logger.warning("⚠️ Panier non trouvé, probablement déjà vidé")
                    panier_vide = True
                    items_removed = 0

            # 🔥 Réponse avec confirmation explicite
            return Response({
                'status': 'succeeded',
                'message': 'Paiement confirmé et panier vidé avec succès',
                'orders_confirmed': orders_updated,
                'transactions_completed': transactions.count(),
                'panier_vide': panier_vide,
                'items_removed': items_removed
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ Erreur confirmation paiement: {e}", exc_info=True)
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
# payments/views.py - Nouvel endpoint

class VerifyCartClearedView(APIView):
    """
    Vérifier que le panier a bien été vidé après paiement
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            panier = Panier.objects.get(user=request.user)
            items_count = panier.items.count()
            
            return Response({
                'cart_empty': items_count == 0,
                'items_count': items_count,
                'verified_at': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Panier.DoesNotExist:
            return Response({
                'cart_empty': True,
                'items_count': 0,
                'message': 'Panier non trouvé (considéré comme vide)'
            }, status=status.HTTP_200_OK)
class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            transaction = Transaction.objects.get(id=id)
            if transaction.user == request.user or transaction.seller == request.user:
                serializer = TransactionSerializer(transaction)
                
                # Récupérer les infos Stripe si disponible
                stripe_data = {}
                if transaction.stripe_payment_intent_id:
                    try:
                        payment_intent = StripeService.retrieve_payment_intent(
                            transaction.stripe_payment_intent_id
                        )
                        stripe_data = {
                            'payment_intent_status': payment_intent.status,
                            'amount_received': payment_intent.amount_received / 100 if payment_intent.amount_received else 0,
                        }
                    except:
                        pass
                
                response_data = serializer.data
                response_data.update(stripe_data)
                
                return Response(response_data, status=status.HTTP_200_OK)
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction non trouvée'}, status=status.HTTP_404_NOT_FOUND)

class RefundView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            transaction = Transaction.objects.get(id=id)

            if request.user != transaction.seller:  # Seul le vendeur peut initier un remboursement
                return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)

            if transaction.status != 'held':
                return Response(
                    {'error': 'Seules les transactions complétées peuvent être remboursées'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Effectuer le remboursement Stripe
            refund = StripeService.create_refund(transaction.stripe_payment_intent_id)
            
            # Mettre à jour la transaction
            transaction.status = 'refunded'
            transaction.stripe_refund_id = refund.id
            transaction.save()

            # Réactiver l'annonce
            listing = transaction.listing
            listing.status = 'active'
            listing.save()

            return Response({
                'status': 'refunded',
                'refund_id': refund.id,
                'message': f'Transaction {transaction.id} remboursée avec succès'
            }, status=status.HTTP_200_OK)

        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction non trouvée'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {'error': f'Erreur de remboursement: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
class PaymentSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Récupérer le récapitulatif de paiement avec les calculs réels
        SANS commission pour l'acheteur
        """
        try:
            # Récupérer le panier de l'utilisateur
            panier = Panier.objects.get(user=request.user)
            panier_items = panier.items.all().select_related('listing')
            
            if not panier_items.exists():
                return Response(
                    {'error': 'Votre panier est vide'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculs réels - SANS commission pour l'acheteur
            sous_total = float(panier.total_price())
            
            # Frais de livraison (vous pouvez adapter cette logique)
            frais_livraison = 1000  # Exemple fixe, à adapter
            
            # Total général = sous-total + frais de livraison seulement
            total_general = sous_total + frais_livraison

            # Détails des articles
            items_details = []
            for item in panier_items:
                item_total = float(item.quantity * item.listing.price)
                items_details.append({
                    'listing_id': item.listing.id,
                    'listing_title': item.listing.title,
                    'quantity': item.quantity,
                    'unit_price': float(item.listing.price),
                    'total_price': item_total,
                })

            response_data = {
                'sous_total': sous_total,
                'frais_livraison': frais_livraison,
                'total_general': total_general,
                'items_count': panier_items.count(),
                'items_details': items_details,
                'currency': 'XOF',
                'note_commission': "La commission de 5% sera déduite lors du transfert au vendeur"
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Panier.DoesNotExist:
            return Response(
                {'error': 'Panier non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"❌ Erreur récupération récapitulatif: {e}")
            return Response(
                {'error': 'Erreur lors du calcul du récapitulatif'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClearCartAfterPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Vider le panier après confirmation du paiement
        """
        try:
            payment_intent_id = request.data.get('payment_intent_id')
            
            if not payment_intent_id:
                return Response(
                    {'error': 'payment_intent_id requis'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier que le paiement est bien réussi
            transactions = Transaction.objects.filter(
                stripe_payment_intent_id=payment_intent_id,
                user=request.user,
                status='held'
            )
            
            if not transactions.exists():
                return Response(
                    {'error': 'Aucune transaction payée trouvée'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vider le panier
            panier = Panier.objects.get(user=request.user)
            panier_items_count = panier.items.count()
            panier.items.all().delete()
            
            logger.info(f"✅ Panier vidé après paiement - User: {request.user.id}, Articles: {panier_items_count}")
            
            return Response({
                'message': f'Panier vidé avec succès ({panier_items_count} articles)',
                'items_removed': panier_items_count
            }, status=status.HTTP_200_OK)
            
        except Panier.DoesNotExist:
            return Response(
                {'error': 'Panier non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"❌ Erreur vidage panier: {e}")
            return Response(
                {'error': 'Erreur lors du vidage du panier'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
# payments/views.py
class PaymentCleanupView(APIView):
    """
    Nettoyer les transactions abandonnées ou échouées
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            payment_intent_id = request.data.get('payment_intent_id')
            
            if payment_intent_id:
                # Supprimer les transactions en pending pour ce payment_intent
                transactions = Transaction.objects.filter(
                    stripe_payment_intent_id=payment_intent_id,
                    user=request.user,
                    status='pending'
                )
                
                deleted_count = transactions.count()
                transactions.delete()
                
                logger.info(f"🧹 Nettoyage transactions - {deleted_count} transactions pending supprimées")
                
                return Response({
                    'message': f'{deleted_count} transactions pending supprimées',
                    'cleaned': True
                }, status=status.HTTP_200_OK)
            
            return Response({'error': 'payment_intent_id requis'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage: {e}")
            return Response(
                {'error': 'Erreur lors du nettoyage'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
