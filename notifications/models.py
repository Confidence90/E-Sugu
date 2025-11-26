from django.db import models
from users.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('order', 'Commande'),
        ('message', 'Message'),
        ('event', 'Événement'),
        ('listing', 'Annonce'),
        ('system', 'Système'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='system')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_display()}] {self.user}: {self.content[:40]}{'...' if len(self.content) > 40 else ''}"
