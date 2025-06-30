from rest_framework import serializers
from .models import Discussion, Message
from users.serializers import UserSerializer  # si tu en as un
from listings.serializers import ListingSerializer  # idem

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'created_at']

class DiscussionSerializer(serializers.ModelSerializer):
    listing = serializers.StringRelatedField()
    buyer = serializers.StringRelatedField()
    seller = serializers.StringRelatedField()
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Discussion
        fields = ['id', 'listing', 'buyer', 'seller', 'created_at', 'messages']

class CreateMessageSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField()
    content = serializers.CharField()
