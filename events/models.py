from django.db import models
from users.models import User
from listings.models import Listing


class Event(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planifié'),
        ('live', 'En direct'),
        ('ended', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    stream_url = models.URLField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.title} ({self.status})"


class EventListing(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='event_listings')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    special_offer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Prix spécial pendant l’événement"
    )

    def __str__(self):
        return f"{self.listing.title} dans {self.event.title}"


class EventMessage(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} dans {self.event.title}"
