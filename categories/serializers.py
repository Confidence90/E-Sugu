from rest_framework import serializers
from .models import Category
class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']
class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)  # ou PrimaryKeyRelatedField si tu veux l'ID

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'parent',
            'subcategories',
            'created_at',
            'updated_at',
        ]
    