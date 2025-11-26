# payments/services/stripe_service.py
import os
import stripe
import logging
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class StripeService:
    
    @staticmethod
    def validate_amount(amount, currency='xof'):
        """
        Valider le montant selon les limites Stripe
        """
        # Convertir en Decimal pour une manipulation précise
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            pass
        else:
            raise ValidationError("Type de montant invalide")
        
        # Pour XOF, le montant doit être entre 1 et 99,999,999
        if currency.lower() == 'xof':
            if amount < 1:
                raise ValidationError("Le montant minimum est 1 XOF")
            if amount > 99999999:
                raise ValidationError("Le montant maximum est 99,999,999 XOF")
        
        return StripeService.get_stripe_amount(amount, currency)

    @staticmethod
    def get_stripe_amount(amount, currency='xof'):
        """
        Convertir le montant selon les règles Stripe
        Pour XOF: montant entier (pas de centimes)
        Pour EUR/USD: montant en centimes/cents
        """
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))
        
        if currency.lower() in ['xof', 'clp', 'pyg', 'jpy']:
            # Devises sans sous-unités - montant entier
            return int(amount)
        else:
            # Devises avec sous-unités - montant en centimes
            return int(amount * 100)

    @staticmethod
    def create_payment_intent(amount, currency='xof', payment_method_types=['card'], **kwargs):
        """
        Créer un PaymentIntent Stripe
        """
        try:
            # Convertir le montant selon les règles Stripe
            stripe_amount = StripeService.get_stripe_amount(amount, currency)
            
            # Valider le montant
            StripeService.validate_amount(amount, currency)
            
            logger.info(f"🔄 Création PaymentIntent: {amount} {currency} (Stripe: {stripe_amount})")
            
            payment_intent = stripe.PaymentIntent.create(
                amount=stripe_amount,
                currency=currency,
                payment_method_types=payment_method_types,
                **kwargs
            )
            
            logger.info(f"✅ PaymentIntent créé: {payment_intent.id}")
            return payment_intent
            
        except stripe.error.InvalidRequestError as e:
            if 'Amount must be' in str(e) or 'amount_too_large' in str(e):
                raise ValidationError("Montant invalide. Le montant doit être compris entre 1 XOF et 99,999,999 XOF.")
            logger.error(f"❌ Requête Stripe invalide: {e}")
            raise ValidationError(f"Erreur de requête: {str(e)}")
        except stripe.error.StripeError as e:
            logger.error(f"❌ Erreur Stripe: {e}")
            raise ValidationError(f"Erreur de traitement du paiement: {str(e)}")
        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"❌ Erreur inattendue: {e}")
            raise ValidationError(f"Erreur lors du traitement du paiement: {str(e)}")

    @staticmethod
    def create_payment_intent_for_mobile(amount, phone, payment_method, currency='xof'):
        """
        Créer un PaymentIntent pour les paiements mobiles
        """
        try:
            logger.info(f"🔄 Création PaymentIntent mobile: {amount} {currency} pour {phone}")
            
            payment_intent = StripeService.create_payment_intent(
                amount=amount,
                currency=currency,
                payment_method_types=['card'],
                metadata={
                    'phone': phone,
                    'payment_method': payment_method,
                    'payment_type': 'mobile'
                }
            )
            
            return payment_intent
            
        except Exception as e:
            logger.error(f"❌ Erreur paiement mobile: {e}")
            raise

    @staticmethod
    def confirm_payment_intent(payment_intent_id, payment_method_id=None):
        """
        Confirmer un PaymentIntent
        """
        try:
            confirm_params = {}
            if payment_method_id:
                confirm_params['payment_method'] = payment_method_id
                
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **confirm_params
            )
            return payment_intent
        except stripe.error.StripeError as e:
            raise ValidationError(f"Erreur de confirmation: {str(e)}")

    @staticmethod
    def retrieve_payment_intent(payment_intent_id):
        """
        Récupérer un PaymentIntent
        """
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            raise ValidationError(f"Erreur de récupération: {str(e)}")

    @staticmethod
    def create_refund(payment_intent_id, amount=None):
        """
        Créer un remboursement
        """
        try:
            refund_data = {'payment_intent': payment_intent_id}
            if amount:
                # Pour XOF, le montant est déjà en unités entières
                refund_data['amount'] = int(amount)
                
            refund = stripe.Refund.create(**refund_data)
            return refund
        except stripe.error.StripeError as e:
            raise ValidationError(f"Erreur de remboursement: {str(e)}")

    @staticmethod
    def create_stripe_account_for_seller(email, country='CI'):
        """
        Créer un compte Connect pour un vendeur (pour les marketplaces)
        """
        try:
            account = stripe.Account.create(
                type='express',
                country=country,
                email=email,
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
            )
            return account
        except stripe.error.StripeError as e:
            raise ValidationError(f"Erreur création compte vendeur: {str(e)}")

    @staticmethod
    def process_panier_payment(panier_items, total_amount, phone, payment_method, currency='xof'):
        """
        Traiter le paiement d'un panier complet
        """
        try:
            logger.info(f"🛒 Traitement paiement panier - Articles: {len(panier_items)}, Total: {total_amount} {currency}")
            
            payment_intent = StripeService.create_payment_intent_for_mobile(
                amount=total_amount,
                phone=phone,
                payment_method=payment_method,
                currency=currency
            )
            
            return payment_intent
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement panier: {e}")
            raise

    @staticmethod
    def process_single_payment(amount, phone, payment_method, currency='xof'):
        """
        Traiter le paiement d'un seul article
        """
        try:
            logger.info(f"🔄 Traitement paiement unique - Montant: {amount} {currency}")
            
            payment_intent = StripeService.create_payment_intent_for_mobile(
                amount=amount,
                phone=phone,
                payment_method=payment_method,
                currency=currency
            )
            
            return payment_intent
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement paiement unique: {e}")
            raise

    @staticmethod
    def check_payment_status(payment_intent_id):
        """
        Vérifier le statut d'un paiement
        """
        try:
            payment_intent = StripeService.retrieve_payment_intent(payment_intent_id)
            return {
                'status': payment_intent.status,
                'amount': payment_intent.amount,
                'currency': payment_intent.currency,
                'created': payment_intent.created,
                'last_payment_error': payment_intent.last_payment_error
            }
        except Exception as e:
            logger.error(f"❌ Erreur vérification statut: {e}")
            raise

    @staticmethod
    def cancel_payment_intent(payment_intent_id):
        """
        Annuler un PaymentIntent
        """
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
            return payment_intent
        except stripe.error.StripeError as e:
            raise ValidationError(f"Erreur d'annulation: {str(e)}")
    
    @staticmethod
    def transfer_to_seller(amount, destination_account_id, currency='xof'):
        """
        Transférer de l'argent à un vendeur via Stripe Connect
        """
        try:
            # Convertir le montant selon les règles Stripe
            stripe_amount = StripeService.get_stripe_amount(amount, currency)
            
            transfer = stripe.Transfer.create(
                amount=stripe_amount,
                currency=currency,
                destination=destination_account_id,
            )
            
            logger.info(f"✅ Transfert effectué: {transfer.id} - {amount} {currency} vers {destination_account_id}")
            return transfer
            
        except stripe.error.StripeError as e:
            logger.error(f"❌ Erreur transfert: {e}")
            raise ValidationError(f"Erreur lors du transfert: {str(e)}")