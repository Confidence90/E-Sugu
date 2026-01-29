# reviews/serializers.py - AJOUTEZ ces sérialiseurs
from rest_framework import serializers
from .models import Review
from users.serializers import UserProfileSerializer
from django.db.models import  Q
from users.models import User

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_details = UserProfileSerializer(source='reviewer', read_only=True)
    reviewed_details = UserProfileSerializer(source='reviewed', read_only=True)
    time_ago = serializers.SerializerMethodField()
    helpful_percentage = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'reviewer_details', 'reviewed', 'reviewed_details',
            'rating', 'comment', 'review_type', 'is_verified_purchase',
            'helpful_count', 'not_helpful_count', 'helpful_percentage',
            'seller_reply', 'reply_date', 'is_edited', 'edit_date',
            'created_at', 'updated_at', 'time_ago', 'can_edit'
        ]
        read_only_fields = ['reviewer', 'created_at', 'updated_at']
    
    def get_time_ago(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(obj.created_at).split(',')[0] + ' ago'
    
    def get_helpful_percentage(self, obj):
        return obj.helpful_score
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return request.user == obj.reviewer
        return False

class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['reviewed', 'rating', 'comment', 'review_type', 'is_verified_purchase']
    
    def validate(self, data):
        # Empêcher les avis sur soi-même
        reviewer = self.context.get('reviewer')
        if reviewer and reviewer == data['reviewed']:
            raise serializers.ValidationError("Vous ne pouvez pas vous évaluer vous-même.")
        
        # Vérifier si l'utilisateur a déjà évalué
        if Review.objects.filter(reviewer=reviewer, reviewed=data['reviewed']).exists():
            raise serializers.ValidationError("Vous avez déjà évalué cet utilisateur.")
        
        return data

class PlatformReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
    
    def create(self, validated_data):
        request = self.context.get('request')
        
        # Récupérer un admin/superutilisateur pour représenter la plateforme
        platform_user = User.objects.filter(
            Q(is_superuser=True) | Q(is_staff=True) | Q(role='admin')
        ).first()
        
        if not platform_user:
            # Si aucun admin n'existe, lever une erreur
            raise serializers.ValidationError("Aucun administrateur trouvé pour la plateforme")
        
        # Vérifier si l'utilisateur a déjà évalué la plateforme
        if Review.objects.filter(
            reviewer=request.user, 
            reviewed=platform_user,
            review_type='platform'
        ).exists():
            raise serializers.ValidationError("Vous avez déjà évalué la plateforme")
        
        # Créer l'avis
        return Review.objects.create(
            reviewer=request.user,
            reviewed=platform_user,
            review_type='platform',
            **validated_data
        )

class ReplySerializer(serializers.Serializer):
    reply = serializers.CharField(required=True, max_length=1000)

class VoteSerializer(serializers.Serializer):
    is_helpful = serializers.BooleanField(required=True)