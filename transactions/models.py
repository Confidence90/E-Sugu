from django.db import models
from commandes.models import Order
from users.models import User


class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('success', 'Succès'),
        ('failed', 'Échec'),
        ('refunded', 'Remboursé'),
    ]

    PAYMENT_METHODS = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('momo', 'Mobile Money'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='transaction')
    # Dans le fichier où se trouve votre modèle Transaction avec order=
    buyer = models.ForeignKey(
    User, 
    on_delete=models.CASCADE, 
    null=True,  # Temporairement nullable
    blank=True,  # Permet un champ vide dans les formulaires
    related_name='transactions'  # Choisissez un related_name approprié
    )
    amount = models.DecimalField(max_digits=10,null=True, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10,null=True, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paymenet_method = models.CharField(max_length=50,null=True, choices=PAYMENT_METHODS)
    stripe_transaction_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction #{self.pk} – {self.status}"


class Revenue(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='revenues')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='revenues')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revenu pour {self.seller} - {self.amount}€"
