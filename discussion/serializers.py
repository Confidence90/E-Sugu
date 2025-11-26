from rest_framework import serializers
from .models import Discussion, Message

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'created_at', 'is_read']

    def get_sender(self, obj):
        return {
            'id': obj.sender.id,
            'username': obj.sender.username,
            'is_staff': obj.sender.is_staff,
            'is_superuser': obj.sender.is_superuser,
            'is_seller': obj.sender.is_seller 
        }

class DiscussionSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Discussion
        fields = [
            'id', 'title', 'participant1', 'participant2', 
            'discussion_type', 'other_participant', 'is_active',
            'created_at', 'updated_at', 'messages', 
            'unread_count', 'last_message'
        ]

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other = obj.get_other_participant(request.user)
            return {
                'id': other.id,
                'username': other.username,
                'email': other.email,
                'is_staff': other.is_staff,
                'is_superuser': other.is_superuser,
                'is_seller': other.is_seller
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'content': last_message.content[:100] + '...' if len(last_message.content) > 100 else last_message.content,
                'created_at': last_message.created_at,
                'sender_username': last_message.sender.username
            }
        return None


class CreateMessageSerializer(serializers.Serializer):
    discussion_id = serializers.IntegerField(required=False)
    recipient_id = serializers.IntegerField(required=False)
    title = serializers.CharField(required=False, max_length=255)  # Pour le sujet de la nouvelle discussion
    content = serializers.CharField()


class CreateDiscussionSerializer(serializers.Serializer):
    recipient_id = serializers.IntegerField()
    title = serializers.CharField(required=False, max_length=255)
    content = serializers.CharField()
    discussion_type = serializers.ChoiceField(
        choices=[('buyer_admin', 'Acheteur ↔ Admin'), ('seller_admin', 'Vendeur ↔ Admin'), ('support', 'Support général')],
        required=False,
        default='support'
    )