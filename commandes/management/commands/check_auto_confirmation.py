# commandes/management/commands/check_auto_confirmation.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from commandes.models import Order
from datetime import timedelta

class Command(BaseCommand):
    help = 'Vérifie les commandes à confirmer automatiquement'
    
    def handle(self, *args, **options):
        self.stdout.write("Vérification des confirmations automatiques...")
        
        # Récupérer les commandes expédiées dont la deadline est dépassée
        expired_orders = Order.objects.filter(
            status='shipped',
            delivery_confirmation_deadline__lte=timezone.now(),
            delivery_confirmed_at__isnull=True
        )
        
        count = 0
        for order in expired_orders:
            success, message = order.confirm_delivery()
            if success:
                count += 1
                self.stdout.write(f"Commande #{order.order_number} auto-confirmée")
        
        self.stdout.write(
            self.style.SUCCESS(f"{count} commande(s) auto-confirmée(s)")
        )
        