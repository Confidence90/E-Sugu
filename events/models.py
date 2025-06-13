# events/models.py
from django.db import models
from users.models import User
from listings.models import Listing

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    stream_url = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('planned', 'Planifié'), ('live', 'En direct'), ('ended', 'Terminé')])
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class EventListing(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_listings')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    special_offer = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

class EventMessage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)