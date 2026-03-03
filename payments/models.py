from django.db import models
from django.utils import timezone
from users.models import User
from listings.models import Listing
from decimal import Decimal
from notifications.models import Notification
from commandes.models import Order, OrderItem
from .services.stripe_service import StripeService
import logging

logger = logging.getLogger(__name__)

class Transaction(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='transactions')
    #buyer = models.ForeignKey(
    #    User,
    #    on_delete=models.CASCADE,
    #    null=True,
    #    blank=True,
    #    related_name='payment_transactions'
    #)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_transactions',null=True,
        blank=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    quantity = models.PositiveIntegerField(default=1) 
    total_amount = models.DecimalField(max_digits=12, null=True, decimal_places=2)  # Montant payé par l'acheteur
    amount = models.DecimalField(max_digits=10, null=True, decimal_places=2)  # Prix unitaire
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.05'))  # 5% de commission
    commission= models.DecimalField(max_digits=10, null=True, decimal_places=2)  # Montant de la commission
    net_amount = models.DecimalField(max_digits=10, null=True, decimal_places=2)  # Montant net pour le vendeur
    status = models.CharField(
        max_length=25, 
        choices=[
            ('pending', 'En attente'),
            ('completed', 'Complété'),
            ('failed', 'Échoué'),
            ('held', 'En escrow'),
            ('refunded', 'Remboursé'),
            ('released', 'Released to seller'),
            ('requires_payment_method', 'Méthode de paiement requise'),
            ('requires_confirmation', 'Confirmation requise'),
            ('requires_action', 'Action requise'),
            ('processing', 'En traitement'),
            ('canceled', 'Annulé'),
            ('transferred', 'Transféré au vendeur')  # Nouveau statut
        ],
        default='pending' 
    )
    order = models.ForeignKey(
        'commandes.Order', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transactions'
    )

    payment_method = models.CharField(max_length=50, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_refund_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_transfer_id = models.CharField(max_length=255, null=True, blank=True)  # ID du transfert vers le vendeur
    stripe_account_id = models.CharField(max_length=255, null=True, blank=True)  # Pour Stripe Connect
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]
    def __str__(self):
        return f"Transaction {self.id} - {self.listing.title}"

    def save(self, *args, **kwargs):
        # S'assurer que amount est Decimal
        if self.amount is not None:
            if isinstance(self.amount, float):
                self.amount = Decimal(str(self.amount))
            elif isinstance(self.amount, int):
                self.amount = Decimal(self.amount)
        
        # Calculs avec Decimal
        if self.amount is not None and self.quantity is not None:
            if self.total_amount is None:
                self.total_amount = self.amount * self.quantity
        
        # Calculs avec Decimal
        if self.total_amount is not None:
            total_decimal = self.total_amount
            
            # Calcul de la commission (5% du total) - pour information seulement
            if self.commission is None:
                self.commission = total_decimal * self.commission_rate
            
            # Calcul du montant net pour le vendeur
            if self.net_amount is None and self.commission is not None:
                self.net_amount = total_decimal - self.commission
        
        super().save(*args, **kwargs)

    def transfer_to_seller(self):
        """
        Transférer l'argent au vendeur après déduction de la commission
        """
        if self.status != 'completed':
            raise ValueError("Le paiement doit être complété avant de transférer au vendeur")
        
        # Ici vous implémenteriez la logique Stripe Connect pour transférer au vendeur
        # Pour l'instant, on met juste à jour le statut
        self.status = 'transferred'
        self.save()
        
        return True
    
    
    
    def create_order_after_payment(self):
        """Créer une commande après paiement réussi"""
        from commandes.models import Order, OrderItem
        
        if self.status == 'completed' and not self.order:
            try:
                logger.info(f"🔄 Création de commande pour transaction {self.id}")
                date_str = timezone.now().strftime('%y%m%d%H%M')  # Format plus court
                order_number = f"ORD-{self.id}-{date_str}"
                # Créer la commande
                order = Order.objects.create(
                    user=self.user, 
                    listing=self.listing, 
                    quantity=self.quantity,  
                    total_price=self.total_amount,
                    status='confirmed',  # Commande confirmée après paiemen     # 🔥 AJOUTER user aussi si nécessaire
                    order_number=order_number,
                    shipping_address="À définir",  # Valeur par défaut
                    customer_notes="Paiement en ligne"
                )
                
                # Créer l'item de commande
                OrderItem.objects.create(
                    order=order,
                    listing=self.listing,
                    quantity=self.quantity,
                    price=self.amount
                )
                self.listing.mark_as_sold(self.quantity)
                self.order = order
                self.save()
                from notifications.models import Notification
                Notification.objects.create(
                    user=self.seller,
                    type='order',
                    content=f'Nouvelle commande #{order.id} pour "{self.listing.title}"'
                )
                logger.info(f"✅ Commande #{order.id} créée pour transaction {self.id}")
                return order
            except Exception as e:
                logger.error(f"❌ Erreur création commande: {e}")
                # 🔥 SOLUTION DE FALLBACK
                return self.create_order_fallback()
        return self.order
    def release_payment_to_seller(self):
        try:
            if self.status != 'held':
                raise ValueError("La transaction doit être en escrow (held)")

            if self.stripe_account_id:
                StripeService.transfer_to_seller(
                    amount=self.net_amount,
                    destination_account_id=self.stripe_account_id
                )

            self.status = 'transferred'
            self.save()

            return True

        except Exception as e:
            logger.error(f"Erreur libération paiement: {e}")
            return False
    
def create_order_fallback(self):
    """Approche simple pour créer une commande (fallback)"""
    try:
        # Format très court pour order_number
        order_number = f"ORD-{self.id}"
        
        # Créer avec seulement les champs absolument requis
        order = Order.objects.create(
           
            user=self.user,
            listing=self.listing,
            quantity=self.quantity,
            total_price=self.total_amount,
            status='confirmed',
            order_number=order_number
        )
        
        # Créer OrderItem séparément
        OrderItem.objects.create(
            order=order,
            listing=self.listing,
            quantity=self.quantity,
            price=self.amount
        )
        
        self.order = order
        self.save()
        logger.info(f"✅ Commande fallback #{order.id} créée")
        return order
        
    except Exception as e:
        logger.error(f"❌ Échec création fallback: {e}")
        return None
    
