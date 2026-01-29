# reviews/models.py
from django.db import models
from users.models import User

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
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created_at']
        unique_together = ['reviewer', 'reviewed']

    def __str__(self):
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