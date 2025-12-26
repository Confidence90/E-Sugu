from django.db import models
from users.models import User
from listings.models import Listing
from django.utils import timezone 


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('ready_to_ship', 'Prêt à expédier'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
        ('failed', 'Échouée'),
        ('returned', 'Retourné'),
    ]
    buyer= models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases', verbose_name='Acheteur')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='orders', verbose_name='Annonce')
    quantity = models.PositiveIntegerField('Quantité commandée',default=1)
    order_number = models.CharField(max_length=50, unique=True, blank=True)  # Numéro unique
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField('Statut',max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_method = models.CharField(max_length=100, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    is_packaged = models.BooleanField(default=False)  # Emballé ou non
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_address = models.TextField('Adresse de livraison',blank=True)
    customer_notes = models.TextField('Notes du client', blank=True)

    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande #{self.id} - {self.listing.title}"

    def update_total(self):
        self.total_price = sum(item.subtotal() for item in self.items.all())
        self.save()
    def save(self, *args, **kwargs):
        # Calcul automatique du prix total
        if not self.total_price:
            self.total_price = self.listing.price * self.quantity
        super().save(*args, **kwargs)
    def confirm_order(self):
        """Confirmer la commande et mettre à jour les stocks"""
        if self.status == 'pending' and self.listing.mark_as_sold(self.quantity):
            self.status = 'confirmed'
            self.save()
            return True
        return False

    def cancel_order(self):
        """Annuler la commande et restocker"""
        if self.status in ['pending', 'confirmed']:
            # Restocker la quantité
            self.listing.quantity_sold = max(0, self.listing.quantity_sold - self.quantity)
            self.listing.update_status_based_on_quantity()
            self.listing.save()
            
            self.status = 'cancelled'
            self.save()
            return True
        return False
    def payment_method(self):
        """Récupère le payment_method depuis la transaction associée"""
        if hasattr(self, 'transaction'):
            return self.transaction.payment_method
        return None

    def pending_since(self):
        """Nombre de jours en attente"""
        if self.status == 'pending':
            return (timezone.now() - self.created_at).days
        return None


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Prix à l'achat

    def __str__(self):
        return f"{self.quantity} x {self.listing.title if self.listing else 'Produit supprimé'}"

    def subtotal(self):
        return self.quantity * self.price
