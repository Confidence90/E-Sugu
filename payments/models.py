from django.db import models
from users.models import User
from listings.models import Listing
from decimal import Decimal

class Transaction(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='transactions')
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='payment_transactions'
    )
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
            ('refunded', 'Remboursé'),
            ('requires_payment_method', 'Méthode de paiement requise'),
            ('requires_confirmation', 'Confirmation requise'),
            ('requires_action', 'Action requise'),
            ('processing', 'En traitement'),
            ('canceled', 'Annulé'),
            ('transferred', 'Transféré au vendeur')  # Nouveau statut
        ],
        default='pending' 
    )
    payment_method = models.CharField(max_length=50, null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_refund_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_transfer_id = models.CharField(max_length=255, null=True, blank=True)  # ID du transfert vers le vendeur
    stripe_account_id = models.CharField(max_length=255, null=True, blank=True)  # Pour Stripe Connect
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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