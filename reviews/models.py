# reviews/models.py
from django.db import models
from users.models import User

class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    reviewed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"

    def __str__(self):
        return f"Avis de {self.reviewer} sur {self.reviewed}"