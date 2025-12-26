# listings/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from users.models import User
from categories.models import Category
import random
from django.utils import timezone

class Listing(models.Model):
    TYPE_CHOICES = [
        ('sale', 'Vente'),
        ('rental', 'Location'),
    ]

    CONDITION_CHOICES = [
        ('new', 'Neuf'),
        ('used', 'Occasion'),
    ]

    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('sold', 'Vendu'),
        ('expired', 'Expiré'),
        ('out_of_stock', 'Epuisé'),
    ]

    title = models.CharField('Titre',max_length=255)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[
            MinValueValidator(1, message="Le prix doit être d'au moins 1 XOF"),
            MaxValueValidator(99999999, message="Le prix ne peut pas dépasser 99,999,999 XOF")
        ]
    )


    quantity = models.PositiveIntegerField('Quantité disponible', default=1)
    quantity_sold = models.PositiveIntegerField('Quantité vendue', default=0)

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='sale')
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    location = models.CharField(max_length=100, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='listings'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listings',
        verbose_name='Utilisateur'
    )

    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Annonce'
        verbose_name_plural = 'Annonces'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    @property
    def available_quantity(self):
        """Quantité réellement disponible"""
        return max(0, self.quantity - self.quantity_sold)

    @property
    def is_out_of_stock(self):
        """Vérifie si le produit est épuisé"""
        return self.available_quantity <= 0

    def update_status_based_on_quantity(self):
        """Met à jour le statut en fonction de la quantité disponible"""
        if self.available_quantity <= 0:
            self.status = 'out_of_stock'
        elif self.status == 'out_of_stock' and self.available_quantity > 0:
            self.status = 'active'
        self.save()

    def mark_as_sold(self, quantity=1):
        """Marquer une quantité comme vendue"""
        if quantity <= self.available_quantity:
            self.quantity_sold += quantity
            self.save()
            was_out_of_stock = self.is_out_of_stock
            self.update_status_based_on_quantity()
            if self.is_out_of_stock and not was_out_of_stock:
                self.send_out_of_stock_notification()
            return True
        return False
    def send_out_of_stock_notification(self):
        """Envoyer une notification d'épuisement de stock"""
        from notifications.models import Notification
        
        try:
            Notification.objects.create(
                user=self.user,
                type='listing',
                content=f'⚠️ Votre produit "{self.title}" est maintenant épuisé. Veuillez réapprovisionner.'
            )
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi de la notification: {e}")
            return False
    
    def send_restock_notification(self):
        """Envoyer une notification de réapprovisionnement"""
        from notifications.models import Notification
        
        try:
            Notification.objects.create(
                user=self.user,
                type='listing',
                content=f'✅ Votre produit "{self.title}" a été réapprovisionné et est maintenant disponible.'
            )
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi de la notification: {e}")
            return False
    def deactivate(self):
        self.status = 'expired'
        self.save()
    def restock(self, new_quantity):
        """Réapprovisionner le produit"""
        self.quantity_sold = max(0, self.quantity_sold - new_quantity)
        self.quantity += new_quantity
        self.update_status_based_on_quantity()
    def clean(self):
        super().clean()
        if self.price > 99999999:
            raise ValidationError({'price': 'Le prix ne peut pas dépasser 99,999,999 XOF'})
    
    def save(self, *args, **kwargs):
        self.full_clean()  # Appelle la validation clean()
        super().save(*args, **kwargs)

    views_count = models.PositiveIntegerField('Nombre de vues', default=0)
    unique_visitors = models.PositiveIntegerField('Visiteurs uniques', default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)
    
    # Méthodes pour le suivi des vues
    def increment_views(self, user=None):
        """Incrémente le compteur de vues"""
        self.views_count += 1
        self.last_viewed = timezone.now()
        
        # Si un utilisateur est fourni et que c'est un visiteur unique
        if user and user.is_authenticated:
            # Vérifier si cette vue a déjà été comptabilisée pour cet utilisateur
            view_key = f"listing_{self.id}_viewed_by_{user.id}"
            from django.core.cache import cache
            if not cache.get(view_key):
                self.unique_visitors += 1
                cache.set(view_key, True, 60*60*24)  # Cache pour 24h
                
        self.save()

class Image(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='listings/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image pour {self.listing.title}"
    
class ListingView(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='views'
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=100, blank=True, null=True) 
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        
        indexes = [
            models.Index(fields=['listing', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
        ]
        ordering = ['-viewed_at']