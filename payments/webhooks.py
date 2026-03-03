# payments/webhooks.py
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import stripe
import json
from django.conf import settings
from .models import Transaction
from django.db import transaction as db_transaction
from paniers.models import Panier
from commandes.models import Order
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)
@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Gérer les événements
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_payment_intent_succeeded(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_intent_failed(payment_intent)

    return HttpResponse(status=200)

def handle_payment_intent_succeeded(payment_intent):
    """
    Version améliorée avec mise à jour du statut de la commande
    """
    payment_intent_id = payment_intent['id']
    
    try:
        # Récupérer les transactions liées
        transactions = Transaction.objects.filter(
            stripe_payment_intent_id=payment_intent_id,
            status='pending'
        ).select_related('user', 'order')
        
        if not transactions.exists():
            logger.info(f"ℹ️ Aucune transaction en attente pour {payment_intent_id}")
            return
        
        with db_transaction.atomic():
            # Mettre à jour les transactions
            for transaction in transactions:
                transaction.status = 'held'
                transaction.held_at = timezone.now()
                transaction.save()
                
                # Marquer le listing comme vendu
                transaction.listing.mark_as_sold(transaction.quantity)
                if transaction.order:
                    order = transaction.order
                    if order.status == 'pending':
                        order.status = 'confirmed'
                        order.save()
                        logger.info(f"✅ Commande #{order.id} confirmée après paiement")
                        
                        # Créer une notification pour le vendeur
                        from notifications.models import Notification
                        Notification.objects.create(
                            user=order.listing.user,
                            type='order_confirmed',
                            content=f'Commande #{order.order_number} confirmée (paiement reçu)'
                        )
            # 🔥 Double vérification : vider le panier si pas déjà fait
            user = transactions.first().user
            try:
                panier = Panier.objects.get(user=user)
                if panier.items.exists():
                    items_count = panier.items.count()
                    panier.items.all().delete()
                    logger.info(f"🔄 Webhook: Panier vidé ({items_count} articles) pour l'utilisateur {user.id}")
                else:
                    logger.info(f"✅ Webhook: Panier déjà vide pour l'utilisateur {user.id}")
            except Panier.DoesNotExist:
                logger.info(f"✅ Webhook: Pas de panier à vider pour l'utilisateur {user.id}")
                
    except Exception as e:
        logger.error(f"❌ Erreur dans le webhook: {e}", exc_info=True)
def handle_payment_intent_failed(payment_intent):
    try:
        transaction = Transaction.objects.get(
            stripe_payment_intent_id=payment_intent['id']
        )
        transaction.status = 'failed'
        transaction.save()
    except Transaction.DoesNotExist:
        pass