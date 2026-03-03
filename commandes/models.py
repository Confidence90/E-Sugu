# commandes/models.py
from django.db import models
from users.models import User
from listings.models import Listing
from django.utils import timezone 
from datetime import timedelta
from payments.services.stripe_service import StripeService
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('ready_to_ship', 'Prête à expédier'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
        # Optionnel :
        ('returned', 'Retour acceptée'),
    ]
    COMPLETED_STATUSES = ['completed', 'confirmed', 'delivered']
    #buyer= models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases', verbose_name='Acheteur')
    #listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='orders', verbose_name='Annonce')
    quantity = models.PositiveIntegerField('Quantité commandée',default=1)
    order_number = models.CharField(max_length=50, unique=True, blank=True)  # Numéro unique
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='Acheteur')
    status = models.CharField('Statut',max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_method = models.CharField(max_length=100, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    is_packaged = models.BooleanField(default=False)  # Emballé ou non
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_address = models.TextField('Adresse de livraison',blank=True)
    customer_notes = models.TextField('Notes du client', blank=True)
    shipped_at = models.DateTimeField('Date d\'expédition', null=True, blank=True)
    delivered_at = models.DateTimeField('Date de livraison', null=True, blank=True)
    delivery_confirmed_at = models.DateTimeField('Date de confirmation réception', null=True, blank=True)
    auto_delivery_reminder_sent = models.BooleanField('Rappel auto envoyé', default=False)
    delivery_confirmation_deadline = models.DateTimeField('Date limite confirmation', null=True, blank=True)
    is_escrow = models.BooleanField('En escrow', default=True)
    held_at = models.DateTimeField('Mis en attente', null=True, blank=True)
    released_at = models.DateTimeField('Libéré', null=True, blank=True)

    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande #{self.id} - {self.listing.title}"

    
    def save(self, *args, **kwargs):
        # Calcul automatique du prix total
        if not self.total_price and self.pk:
            self.total_price = sum(item.subtotal() for item in self.items.all())
        super().save(*args, **kwargs)
    def confirm_order(self):
        """Confirmer la commande et mettre à jour les stocks"""
        if self.status == 'pending' and self.listing.mark_as_sold(self.quantity):
            self.status = 'confirmed'
            self.save()
            return True
        return False
    def update_total(self):
        self.total_price = sum(item.subtotal() for item in self.items.all())
        
        self.save()
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
    def mark_as_shipped(self):
        """Marquer la commande comme expédiée"""
        self.status = 'shipped'
        self.shipped_at = timezone.now()
        # Définir la date limite de confirmation (7 jours plus tard)
        self.delivery_confirmation_deadline = timezone.now() + timedelta(days=7)
        self.save()
        
        # Créer des notifications
        from notifications.models import Notification
        
        # Notification à l'acheteur
        Notification.objects.create(
            user=self.user,
            type='order_shipped',
            content=f'Votre commande #{self.order_number} a été expédiée. Pensez à confirmer la réception !'
        )
        
        # Notification à l'admin
        admin_users = User.objects.filter(is_staff=True, is_superuser=True)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                type='order_shipped',
                content=f'Commande #{self.order_number} expédiée'
            )
        
        return True
    
    def confirm_delivery(self, confirmed_by=None):
        """Confirmer la réception de la commande"""
        if self.status != 'shipped':
            return False, "La commande doit être expédiée pour être confirmée"
        if self.delivery_confirmed_at:  # Déjà confirmée
            return False, "Cette commande a déjà été confirmée"
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.delivery_confirmed_at = timezone.now()
        
        # Si confirmé par un utilisateur spécifique (admin ou acheteur)
        if confirmed_by:
            self.delivery_confirmed_by = confirmed_by
        
        self.save()
        
        # 🔥 Déclencher le paiement au vendeur (si escrow)
        self.release_payment_to_seller()
        
        # Créer des notifications
        from notifications.models import Notification
        
        # Notification au vendeur
        sellers_notified = set()
        for item in self.items.all():
            if item.listing and item.listing.user:
                seller = item.listing.user
                if seller.id not in sellers_notified:
                    Notification.objects.create(
                        user=seller,
                        type='order_delivered',
                        content=f'Commande #{self.order_number} confirmée livrée par l\'acheteur'
                    )
                    sellers_notified.add(seller.id)
        
        # Notification à l'admin
        admin_users = User.objects.filter(is_staff=True, is_superuser=True)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                type='order_delivered',
                content=f'Commande #{self.order_number} livrée et confirmée'
            )
        
        return True, "Livraison confirmée avec succès"
    def check_auto_confirmation(self):
        """Vérifier si la commande doit être auto-confirmée"""
        if (self.status == 'shipped' and 
            self.delivery_confirmation_deadline and 
            timezone.now() >= self.delivery_confirmation_deadline):
            
            # Auto-confirmation
            self.confirm_delivery()
            
            # Notification spéciale
            from notifications.models import Notification
            Notification.objects.create(
                user=self.user,
                type='auto_confirmed',
                content=f'Votre commande #{self.order_number} a été automatiquement confirmée après 7 jours'
            )
            
            return True
        return False
   

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Prix à l'achat

    def __str__(self):
        return f"{self.quantity} x {self.listing.title if self.listing else 'Produit supprimé'}"

    def subtotal(self):
        return self.quantity * self.price
    
 