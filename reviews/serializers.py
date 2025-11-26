# reviews/serializers.py
from rest_framework import serializers
from .models import Review
from users.serializers import UserProfileSerializer

class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserProfileSerializer(read_only=True)
    reviewed = UserProfileSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'reviewer', 'reviewed', 'rating', 'comment', 'created_at']

class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['reviewed', 'rating', 'comment']