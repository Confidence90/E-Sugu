# favorites/models.py
from django.db import models
from users.models import User
from listings.models import Listing
from events.models import Event

class FavoriteListing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_listings')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ['user', 'listing']

class FavoriteEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_events')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        unique_together = ['user', 'event']