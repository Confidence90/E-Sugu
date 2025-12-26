# listings/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Listing
from commandes.models import Order
from notifications.models import Notification

@receiver(post_save, sender=Listing)
def check_stock_after_save(sender, instance, **kwargs):
    """Vérifier le stock après chaque sauvegarde d'une annonce"""
    if instance.is_out_of_stock and instance.status != 'out_of_stock':
        # Le produit vient de s'épuiser
        instance.status = 'out_of_stock'
        instance.save(update_fields=['status'])
        
        # Envoyer la notification
        Notification.objects.create(
            user=instance.user,
            type='listing',
            content=f'⚠️ Stock épuisé ! Votre produit "{instance.title}" n\'est plus disponible. Veuillez réapprovisionner.'
        )

@receiver(post_save, sender=Order)
def check_stock_after_order(sender, instance, created, **kwargs):
    """Vérifier le stock après chaque commande"""
    if created and instance.status == 'confirmed':
        listing = instance.listing
        
        # Vérifier si la commande épuise le stock
        if listing.available_quantity <= 0:
            # Envoyer une notification d'épuisement
            Notification.objects.create(
                user=listing.user,
                type='listing',
                content=f'⚠️ Votre produit "{listing.title}" vient d\'être épuisé après une commande. Stock restant: 0'
            )
            
            # Marquer comme épuisé
            listing.status = 'out_of_stock'
            listing.save(update_fields=['status'])