# messages/serializers.py
from rest_framework import serializers
from .models import Message
from users.serializers import UserProfileSerializer
from listings.serializers import ListingSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserProfileSerializer(read_only=True)
    receiver = UserProfileSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'listing', 'sender', 'receiver', 'content', 'timestamp']

class CreateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['listing', 'receiver', 'content']