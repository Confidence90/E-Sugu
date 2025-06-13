# listings/serializers.py
from rest_framework import serializers
from .models import Listing, Image
from users.serializers import UserProfileSerializer
from categories.serializers import CategorySerializer
from categories.models import Category


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image', 'created_at']

class ListingSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = ['id', 'title', 'description', 'price', 'condition', 'category', 'category_id', 'location', 'status', 'user', 'images', 'created_at']

    def validate_category_id(self, value):
        try:
            Category.objects.get(id=value)
        except Category.DoesNotExist:
            raise serializers.ValidationError("Catégorie non trouvée")
        return value

class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()