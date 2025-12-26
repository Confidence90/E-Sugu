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
from .serializers import TransactionSerializer, CreateTransactionSerializer, PaymentConfirmationSerializer
from .services.stripe_service import StripeService

logger = logging.getLogger(__name__)

# payments/views.py
# payments/views.py
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
from django.db import transaction as db_transaction
from .models import Transaction
from listings.models import Listing
from paniers.models import Panier, PanierItem  # Import des modèles panier
from .serializers import TransactionSerializer, CreateTransactionSerializer, PaymentConfirmationSerializer
from .services.stripe_service import StripeService

logger = logging.getLogger(__name__)

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
        """
        Traiter le paiement du panier complet
        """
        try:
            # RÉCUPÉRATION ET VALIDATION DU PANIER
            panier = Panier.objects.get(user=request.user)
            panier_items = panier.items.all().select_related('listing')
            
            if not panier_items.exists():
                print("❌ Panier vide détecté lors de la vérification initiale")
                return Response(
                    {'error': 'Votre panier est vide. Impossible de procéder au paiement.'}, 
                    status=status.HTTP_400_BAD_REQUEST
            )
            print(f"🛒 Panier trouvé: {panier_items.count()} articles")
            for item in panier_items:
                print(f"  - {item.listing.title} x{item.quantity}")
            
            # VALIDATION DU PANIER
            can_create, validation_message = panier.can_create_order()
            if not can_create:
                return Response(
                    {'error': validation_message}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # CALCUL DU MONTANT TOTAL DU PANIER
            total_amount = float(panier.total_price())
            
            logger.info(f"🛒 Paiement panier - User: {request.user.id}, Articles: {panier_items.count()}, Total: {total_amount} XOF")
            
            # VALIDATION DU MONTANT
            try:
                StripeService.validate_amount(total_amount, 'xof')
            except ValidationError as e:
                return Response(
                    {'error': f'Montant invalide: {str(e)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # VÉRIFICATION DU NUMÉRO DE TÉLÉPHONE
            if not request.user.phone:
                return Response(
                    {'error': 'Numéro de téléphone requis pour effectuer un paiement'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # CRÉATION DU PAIEMENT STRIPE
            phone_full = f"{request.user.country_code}{request.user.phone}"
            
            payment_intent = StripeService.create_payment_intent_for_mobile(
                amount=total_amount,
                phone=phone_full,  # Utilisation de 'phone' au lieu de 'phone_number'
                payment_method=payment_method
            )
            stripe.PaymentIntent.modify(
                payment_intent.id,
                metadata={
                    'user_id': str(request.user.id),
                    'payment_type': 'panier'
                }
            )
            
            # CRÉATION DES TRANSACTIONS DANS UNE TRANSACTION BDD
            with db_transaction.atomic():
                transactions = []
                total_commission = Decimal('0.00')
                total_net_amount = Decimal('0.00')
                
                
                for panier_item in panier_items:
                    # Calcul des montants pour cet article
                    item_total_amount = panier_item.quantity * panier_item.listing.price
                    item_commission = item_total_amount * Decimal('0.07')
                    item_net_amount = item_total_amount - item_commission
                    
                    # Créer une transaction pour chaque article du panier
                    transaction = Transaction(
                        listing=panier_item.listing,
                        buyer=request.user,
                        seller=panier_item.listing.user,
                        quantity=panier_item.quantity,
                        amount=panier_item.listing.price,  # Prix unitaire
                        total_amount=item_total_amount,  # Total pour cet article
                        commission=item_commission,
                        net_amount=item_net_amount,
                        status='pending',
                        payment_method=payment_method,
                        stripe_payment_intent_id=payment_intent.id
                    )
                    
                    transaction.save()
                    transactions.append(transaction)
                    
                    # Accumuler les totaux
                    total_commission += item_commission
                    total_net_amount += item_net_amount
                    
                    logger.info(f"✅ Transaction créée: {transaction.id} - {panier_item.listing.title} x{panier_item.quantity}")
                
                # VIDER LE PANIER après création des transactions
               
                logger.info(f"🛒 Panier vidé après création des transactions")
            
            # PRÉPARATION DE LA RÉPONSE
            response_data = {
                'status': 'requires_payment_method',
                'transaction_ids': [t.id for t in transactions],
                'payment_intent_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'total_amount': total_amount,
                'total_commission': float(total_commission),
                'total_net_amount': float(total_net_amount),
                'items_count': len(transactions),
                'currency': 'xof',
                'items': [
                    {
                        'listing_id': t.listing.id,
                        'listing_title': t.listing.title,
                        'quantity': t.quantity,
                        'unit_price': float(t.amount),
                        'total_price': float(t.total_amount),
                        'commission': float(t.commission),
                        'net_amount': float(t.net_amount)
                    }
                    for t in transactions
                ]
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Panier.DoesNotExist:
            logger.warning(f"⚠️ Panier non trouvé pour l'utilisateur: {request.user.id}")
            return Response(
                {'error': 'Panier non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            logger.error(f"❌ Erreur de validation: {e}")
            return Response(
                {'error': f'Erreur de paiement: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors du paiement panier: {e}", exc_info=True)
            return Response(
                {'error': 'Erreur interne lors du traitement du paiement'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Duplicate definition removed: process_panier_payment

    def get(self, request):
        """
        Récupérer les transactions de l'utilisateur
        """
        try:
            transactions = Transaction.objects.filter(buyer=request.user) | Transaction.objects.filter(seller=request.user)
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"❌ Erreur récupération transactions: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération des transactions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# payments/views.py - Dans PaymentConfirmationView
# payments/views.py
class PaymentConfirmationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"🔍 Confirmation paiement - User: {request.user.id}, Data: {request.data}")
        serializer = PaymentConfirmationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_intent_id = serializer.validated_data['payment_intent_id']

        try:
            # 🔥 Toujours filtrer uniquement les transactions en attente
            transactions = Transaction.objects.filter(
                stripe_payment_intent_id=payment_intent_id,
                buyer=request.user,
                status='pending'
            )

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

            # 🔥 Paiement OK → traitement atomique
            with db_transaction.atomic():

                orders_created = []
                order_numbers = []
                
                for transaction in transactions:
                    # Mettre la transaction en completed
                    transaction.status = 'completed'
                    transaction.save()

                    # 🎯 CASE 1 : Une commande existe déjà → on confirme juste
                    if transaction.order:
                        transaction.order.status = 'confirmed'
                        transaction.order.save()

                        orders_created.append(transaction.order)
                        order_numbers.append(transaction.order.order_number)

                    else:
                        # 🎯 CASE 2 : Créer une nouvelle commande
                        try:
                            order = transaction.create_order_after_payment()
                        

                            if order:
                                orders_created.append(order)
                                order_numbers.append(order.order_number)
                                logger.info(f"✅ Commande créée #{order.id}")
                            else:
                                logger.error(f"❌ Impossible de créer une commande pour transaction {transaction.id}")
                        except Exception as e:
                            logger.error(f"❌ Erreur création commande: {e}")
                            logger.info("➡️ Tentative fallback…")
                            order = transaction.create_order_fallback()
                            continue
                    # 🔥 Mise à jour du listing vendu
                    try:
                        transaction.listing.mark_as_sold(transaction.quantity)
                    except Exception as e:
                        logger.error(f"❌ Erreur mise à jour annonce: {e}")

                # 🔥 Vider le panier
                try:
                    panier = Panier.objects.get(user=request.user)
                    items_removed = panier.items.count()
                    panier.items.all().delete()
                    panier_vide = True
                    logger.info(f"🛒 Panier vidé ({items_removed} articles)")
                except Panier.DoesNotExist:
                    panier_vide = False
                    items_removed = 0
                    logger.warning("⚠️ Aucun panier trouvé")

            # 🔥 Réponse complète
            return Response({
                'status': 'succeeded',
                'message': f'Paiement confirmé - {len(orders_created)} commande(s) traitée(s)',
                'transactions_completed': transactions.count(),
                'orders_created': [order.id for order in orders_created],
                'orders_numbers': order_numbers,
                'panier_vide': panier_vide,
                'items_removed': items_removed
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ Erreur confirmation paiement: {e}", exc_info=True)
            return Response(
                {'error': f'Erreur interne: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            transaction = Transaction.objects.get(id=id)
            if transaction.buyer == request.user or transaction.seller == request.user:
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

            if transaction.status != 'completed':
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
                buyer=request.user,
                status='completed'
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
                    buyer=request.user,
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
        
