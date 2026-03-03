# commandes/management/commands/auto_confirm_deliveries.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from commandes.models import Order

class Command(BaseCommand):
    help = 'Confirme automatiquement les commandes après 7 jours'
    
    def handle(self, *args, **options):
        # Commandes expédiées dont la deadline est dépassée
        orders_to_confirm = Order.objects.filter(
            status='shipped',
            delivery_confirmation_deadline__lte=timezone.now(),
            delivery_confirmed_at__isnull=True
        )
        
        for order in orders_to_confirm:
            order.confirm_delivery()  # Auto-confirmation
            self.stdout.write(f"✅ Commande #{order.id} auto-confirmée")