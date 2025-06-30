# payments/models.py
from django.db import models
from users.models import User
from listings.models import Listing

class Transaction(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='transactions')
    # Dans payments/models.py
    buyer = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    null=True,  # Temporairement nullable
    blank=True,
    related_name='payment_transactions'  # Gardez cohérent avec l'existant
    )
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    amount = models.DecimalField(max_digits=10,null=True, decimal_places=2)
    commission = models.DecimalField(max_digits=10,null=True, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10,null=True, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'En attente'), ('completed', 'Complété'), ('failed', 'Échoué'), ('refunded', 'Remboursé')])
    payment_method = models.CharField(max_length=50,null=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.id} - {self.listing.title}"