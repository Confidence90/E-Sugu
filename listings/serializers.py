# listings/serializers.py
from rest_framework import serializers
from .models import Listing, Image
from categories.models import Category

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image', 'created_at']

class ListingSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Listing
        fields = '__all__'
    def validate_category(self, value):
        if not Category.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Catégorie non trouvée.")
        return value

class ListingCreateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'price', 'type', 'condition', 'location',
            'category', 'images', 'is_featured'
        ]

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        listing = Listing.objects.create(**validated_data, user=self.context['request'].user)
        for image in images:
            Image.objects.create(listing=listing, image=image)
        return listing
    def validate_category(self, value):
        if not Category.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Catégorie invalide ou inexistante.")
        return value


class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['image']