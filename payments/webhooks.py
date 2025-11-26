# payments/webhooks.py
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import stripe
import json
from django.conf import settings
from .models import Transaction

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
    try:
        transaction = Transaction.objects.get(
            stripe_payment_intent_id=payment_intent['id']
        )
        transaction.status = 'completed'
        transaction.save()
        
        # Marquer l'annonce comme vendue
        transaction.listing.status = 'sold'
        transaction.listing.save()
    except Transaction.DoesNotExist:
        pass

def handle_payment_intent_failed(payment_intent):
    try:
        transaction = Transaction.objects.get(
            stripe_payment_intent_id=payment_intent['id']
        )
        transaction.status = 'failed'
        transaction.save()
    except Transaction.DoesNotExist:
        pass