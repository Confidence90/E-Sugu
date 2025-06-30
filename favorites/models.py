from django.db import models
from users.models import User
from listings.models import Listing
from events.models import Event

class FavoriteListing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_listings')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ['user', 'listing']
        verbose_name = 'Annonce favorite'
        verbose_name_plural = 'Annonces favorites'

    def __str__(self):
        return f"{self.user} ❤️ {self.listing}"

class FavoriteEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_events')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ['user', 'event']
        verbose_name = 'Événement favori'
        verbose_name_plural = 'Événements favoris'

    def __str__(self):
        return f"{self.user} 🌟 {self.event}"
