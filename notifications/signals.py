# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from users.models import User
from commandes.models import Order
from listings.models import Listing
from .models import Notification

@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """Créer une notification pour les nouvelles commandes"""
    if created:
        # Notification pour l'admin
        Notification.objects.create(
            admin_only=True,
            type='order',
            content=f"Nouvelle commande #{instance.id} de {instance.buyer.email}",
            data={
                'order_id': instance.id,
                'buyer_id': instance.buyer.id,
                'buyer_email': instance.buyer.email,
                'total': float(instance.total_price),
                'status': instance.status
            },
            priority='high'
        )
        
        # Notification pour le vendeur
        if instance.listing.user:
            Notification.objects.create(
                user=instance.listing.user,
                type='order',
                content=f"Nouvelle commande #{instance.id} pour votre produit {instance.listing.title}",
                data={'order_id': instance.id}
            )

@receiver(post_save, sender=User)
def create_user_notification(sender, instance, created, **kwargs):
    """Créer une notification pour les nouveaux vendeurs en attente"""
    if created and instance.is_seller and instance.is_seller_pending:
        Notification.objects.create(
            admin_only=True,
            type='user',
            content=f"Nouveau vendeur en attente: {instance.email}",
            data={
                'user_id': instance.id,
                'email': instance.email,
                'full_name': instance.get_full_name()
            },
            priority='medium'
        )

@receiver(post_save, sender=Listing)
def create_stock_notification(sender, instance, **kwargs):
    """Créer une notification pour les stocks épuisés"""
    if instance.is_out_of_stock and instance.status == 'out_of_stock':
        # Notification au vendeur (existe déjà)
        # Notification admin pour suivi
        Notification.objects.create(
            admin_only=True,
            type='listing',
            content=f"Produit épuisé: {instance.title} (Vendeur: {instance.user.email})",
            data={
                'listing_id': instance.id,
                'seller_id': instance.user.id,
                'seller_email': instance.user.email,
                'title': instance.title
            },
            priority='low'
        )