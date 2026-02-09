# notifications/serializers.py
from rest_framework import serializers
from .models import Notification
from users.serializers import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'content', 'is_read', 'is_handled', 'priority', 'created_at']

class AdminNotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    handled_by = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'admin_only', 'type', 'content', 'data', 
            'is_read', 'is_handled', 'handled_by', 'handled_at',
            'priority', 'created_at', 'expires_at', 'created_by'
        ]
        read_only_fields = ['created_at', 'handled_at', 'expires_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)

