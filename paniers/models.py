from django.db import models
from users.models import User
from listings.models import Listing


class Panier(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paniers')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Panier de {self.user}"

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())
    def can_create_order(self):
        """Vérifie si toutes les quantités dans le panier sont disponibles"""
        for item in self.items.all():
            if item.quantity > item.listing.available_quantity:
                return False, f"Quantité insuffisante pour {item.listing.title}. Stock disponible: {item.listing.available_quantity}"
        return True, ""


class PanierItem(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('panier', 'listing')

    def __str__(self):
        return f"{self.quantity} x {self.listing.title}"

    def total_price(self):
        return self.quantity * self.listing.price
    def is_available(self):
        """Vérifie si la quantité demandée est disponible"""
        return self.quantity <= self.listing.available_quantity
    
    def get_available_quantity(self):
        """Retourne la quantité maximale disponible"""
        return min(self.quantity, self.listing.available_quantity)
