# listings/models.py
from django.db import models
from users.models import User
from categories.models import Category

class Listing(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=20, choices=[('new', 'Neuf'), ('used', 'Occasion')])
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='listings')
    location = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=[('active', 'Actif'), ('sold', 'Vendu'), ('expired', 'Expiré')], default='active')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Image(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/%Y/%m/%d/')
    created_at = models.DateTimeField(auto_now_add=True)