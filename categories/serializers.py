from rest_framework import serializers
from .models import Category

class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.StringRelatedField(read_only=True)  # ou PrimaryKeyRelatedField si tu veux l'ID

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'description',
            'image',
            'parent',
            'created_at',
            'updated_at',
        ]
