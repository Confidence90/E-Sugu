# payments/management/commands/debug_payment.py
from django.core.management.base import BaseCommand
from listings.models import Listing
from payments.services.stripe_service import StripeService

class Command(BaseCommand):
    help = 'Debugger le problème de paiement'

    def handle(self, *args, **options):
        self.stdout.write('🐛 Debuggage du problème de paiement...')
        
        # Vérifier l'annonce ID 2
        try:
            listing = Listing.objects.get(id=2)
            self.stdout.write(f'📦 Annonce trouvée: {listing.title}')
            self.stdout.write(f'💰 Prix: {listing.price} XOF')
            self.stdout.write(f'💰 Type: {type(listing.price)}')
            
            # Tester la validation
            try:
                StripeService.validate_amount(float(listing.price), 'xof')
                self.stdout.write(self.style.SUCCESS('✅ Validation du prix: OK'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Validation échouée: {e}'))
            
            # Tester la création du PaymentIntent
            try:
                payment_intent = StripeService.create_payment_intent(
                    amount=float(listing.price),
                    currency='xof'
                )
                self.stdout.write(self.style.SUCCESS(f'✅ PaymentIntent créé: {payment_intent.id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ PaymentIntent échoué: {e}'))
                
        except Listing.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ Annonce non trouvée'))