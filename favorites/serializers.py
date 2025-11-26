from rest_framework import serializers
from .models import FavoriteListing, FavoriteEvent
from listings.models import Listing
from listings.serializers import ListingSerializer
from events.models import Event
from events.serializers import EventSerializer

class FavoriteListingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.IntegerField(write_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = FavoriteListing
        fields = ['id', 'user', 'listing', 'listing_id']
        read_only_fields = ['user']

    def validate_listing_id(self, value):
        if not Listing.objects.filter(id=value).exists():
            raise serializers.ValidationError("Annonce non trouvée.")
        return value

    def create(self, validated_data):
        listing_id = validated_data.pop('listing_id')
        listing = Listing.objects.get(id=listing_id)
        return FavoriteListing.objects.create(user=self.context['request'].user, listing=listing)

class FavoriteEventSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    event_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = FavoriteEvent
        fields = ['id', 'user', 'event', 'event_id']
        read_only_fields = ['user']


   # def validate_event_id(self, value):
    #    if not Event.objects.filter(id=value).exists():
    #        raise serializers.ValidationError("Événement non trouvé.")
    #    return value

    #def create(self, validated_data):
    #    event_id = validated_data.pop('event_id')
    #    event = Event.objects.get(id=event_id)
    #    return FavoriteEvent.objects.create(user=self.context['request'].user, event=event)
