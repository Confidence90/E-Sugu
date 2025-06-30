from django.db import models
from users.models import User
from categories.models import Category


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
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='sale')
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
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
        related_name='listings'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Annonce'
        verbose_name_plural = 'Annonces'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def mark_as_sold(self):
        self.status = 'sold'
        self.save()

    def deactivate(self):
        self.status = 'expired'
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
