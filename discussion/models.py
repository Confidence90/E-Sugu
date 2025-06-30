from django.db import models
from users.models import User
from listings.models import Listing


class Discussion(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='discussions'
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_buyer'
    )
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_seller'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('listing', 'buyer', 'seller')
        ordering = ['-created_at']

    def __str__(self):
        return f"Discussion {self.id} : {self.buyer} ↔ {self.seller} ({self.listing.title})"


class Message(models.Model):
    discussion = models.ForeignKey(
        Discussion,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.discussion.listing.title}"
