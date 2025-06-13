# events/serializers.py
from rest_framework import serializers
from .models import Event, EventListing, EventMessage
from listings.serializers import ListingSerializer
from users.serializers import UserProfileSerializer

class EventListingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = EventListing
        fields = ['id', 'listing', 'special_offer']

class EventMessageSerializer(serializers.ModelSerializer):
    sender = UserProfileSerializer(read_only=True)

    class Meta:
        model = EventMessage
        fields = ['id', 'sender', 'content', 'timestamp']

class EventSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    event_listings = EventListingSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'start_time', 'end_time', 'stream_url', 'status', 'user', 'event_listings', 'created_at']

class CreateEventSerializer(serializers.ModelSerializer):
    listing_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    special_offer = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)

    class Meta:
        model = Event
        fields = ['title', 'description', 'start_time', 'listing_ids', 'special_offer']

class CreateEventMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventMessage
        fields = ['content']