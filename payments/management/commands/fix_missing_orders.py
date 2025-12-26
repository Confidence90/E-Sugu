# create_management/commands/fix_missing_orders.py
from django.core.management.base import BaseCommand
from transactions.models import Transaction
from commandes.models import Order, OrderItem
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Réparer les commandes manquantes pour les transactions complétées'

    def handle(self, *args, **options):
        # Trouver toutes les transactions complétées sans commande
        transactions_without_orders = Transaction.objects.filter(
            status='completed',
            order__isnull=True
        )
        
        self.stdout.write(f"📊 Transactions sans commande: {transactions_without_orders.count()}")
        
        orders_created = 0
        
        for transaction in transactions_without_orders:
            try:
                # Vérifier si une commande existe déjà pour ce buyer/listing
                existing_order = Order.objects.filter(
                    user=transaction.buyer,
                    listing=transaction.listing,
                    created_at__date=transaction.created_at.date()
                ).first()
                
                if existing_order:
                    # Lier la transaction à la commande existante
                    transaction.order = existing_order
                    transaction.save()
                    self.stdout.write(f"✅ Transaction {transaction.id} liée à commande existante #{existing_order.id}")
                else:
                    # Créer une nouvelle commande
                    order_number = f"REPAIR-{transaction.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                    
                    order = Order.objects.create(
                        user=transaction.buyer,
                        buyer=transaction.buyer,
                        listing=transaction.listing,
                        quantity=transaction.quantity,
                        total_price=transaction.total_amount,
                        status='confirmed',
                        order_number=order_number,
                        shipping_address="Adresse non spécifiée (réparée)",
                        customer_notes="Commande créée automatiquement lors de la réparation"
                    )
                    
                    # Créer l'item de commande
                    OrderItem.objects.create(
                        order=order,
                        listing=transaction.listing,
                        quantity=transaction.quantity,
                        price=transaction.amount
                    )
                    
                    # Lier la transaction à la nouvelle commande
                    transaction.order = order
                    transaction.save()
                    
                    orders_created += 1
                    self.stdout.write(f"✅ Commande #{order.id} créée pour transaction {transaction.id}")
                    
            except Exception as e:
                self.stderr.write(f"❌ Erreur transaction {transaction.id}: {str(e)}")
        
        self.stdout.write(self.style.SUCCESS(f"✅ Réparation terminée: {orders_created} nouvelles commandes créées"))