# reviews/models.py
from django.db import models
from users.models import User
from django.db.models import  Q

# reviews/models.py - AJOUTEZ ces champs
class Review(models.Model):
    RATING_CHOICES = [
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    ]
    
    TYPE_CHOICES = [
        ('seller', 'Vendeur'),
        ('buyer', 'Acheteur'),
        ('product', 'Produit'),
        ('platform', 'Plateforme'),
    ]
    
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    review_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='seller')
    is_verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)
    seller_reply = models.TextField(blank=True, null=True)
    reply_date = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    edit_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.SET_NULL,  # Important pour ne pas perdre les avis si l'annonce est supprimée
        null=True,  # 🔥 TRÈS IMPORTANT : permet les avis sans listing
        blank=True,
        related_name='reviews',
        help_text='Annonce spécifique évaluée (pour les avis produits)'
    )
    
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['reviewer', 'listing'],
                name='unique_review_per_user_per_listing',
                condition=Q(listing__isnull=False)  # 🔥 S'applique seulement quand il y a un listing
            ),
            models.UniqueConstraint(
                fields=['reviewer', 'reviewed', 'review_type'],
                name='unique_user_review_for_non_product',
                condition=Q(listing__isnull=True) & ~Q(review_type='product')  # 🔥 Pour avis non-produits
            )
        ]

    def __str__(self):
        if self.listing:
            return f"Avis de {self.reviewer} sur {self.listing.title} - {self.rating}★"
        return f"Avis de {self.reviewer} sur {self.reviewed} - {self.rating}★"

    @property
    def helpful_score(self):
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return (self.helpful_count / total) * 100

    def update_rating_stats(self):
        """Mettre à jour les statistiques de l'utilisateur évalué"""
        from django.db.models import Avg, Count
        stats = Review.objects.filter(reviewed=self.reviewed).aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id')
        )
        
        # Mettre à jour le profil utilisateur ou vendeur
        self.reviewed.average_rating = stats['avg_rating'] or 0
        self.reviewed.total_reviews = stats['total_reviews'] or 0
        self.reviewed.save()
    
    def clean(self):
        """Validation personnalisée"""
        from django.core.exceptions import ValidationError
        
        # Pour les avis produits, un listing est requis
        if self.review_type == 'product' and not self.listing:
            raise ValidationError({
                'listing': 'Un avis produit doit être lié à une annonce.'
            })
        
        # Pour les avis non-produits, pas de listing
        if self.review_type in ['seller', 'buyer', 'platform'] and self.listing:
            raise ValidationError({
                'listing': f'Un avis {self.get_review_type_display()} ne doit pas être lié à une annonce.'
            })
        
        # Un utilisateur ne peut pas s'auto-évaluer
        if self.reviewer == self.reviewed:
            raise ValidationError({
                'reviewed': 'Vous ne pouvez pas vous évaluer vous-même.'
            })
    def save(self, *args, **kwargs):
        self.full_clean()  # Appelle la validation
        super().save(*args, **kwargs)