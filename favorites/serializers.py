# favorites/serializers.py
from rest_framework import serializers
from .models import FavoriteListing, FavoriteEvent
from listings.serializers import ListingSerializer
from events.serializers import EventSerializer

class FavoriteListingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FavoriteListing
        fields = ['id', 'user', 'listing', 'listing_id']
        read_only_fields = ['user']

class FavoriteEventSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    event_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FavoriteEvent
        fields = ['id', 'user', 'event', 'event_id']
        read_only_fields = ['user']