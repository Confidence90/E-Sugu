from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Discussion, Message
from .serializers import DiscussionSerializer, MessageSerializer, CreateMessageSerializer, CreateDiscussionSerializer
from users.models import User
from django.db import models

class DiscussionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DiscussionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Seules les discussions impliquant l'admin sont autorisées
        if user.is_staff or user.is_superuser:
            # Admin voit toutes les discussions où il est participant
            return Discussion.objects.filter(
                models.Q(participant1=user) | models.Q(participant2=user),
                is_active=True
            )
        else:
            # Utilisateurs normaux voient seulement leurs discussions avec l'admin
            admin_users = User.objects.filter(models.Q(is_staff=True) | models.Q(is_superuser=True))
            return Discussion.objects.filter(
                (
                    (models.Q(participant1=user) & models.Q(participant2__in=admin_users)) |
                    (models.Q(participant2=user) & models.Q(participant1__in=admin_users))
                ),
                is_active=True
            )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def retrieve(self, request, *args, **kwargs):
        """Récupérer une discussion et marquer les messages comme lus"""
        instance = self.get_object()
        
        # Marquer les messages comme lus pour l'utilisateur actuel
        instance.mark_as_read_for_user(request.user)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SendMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreateMessageSerializer(data=request.data)
        if serializer.is_valid():
            discussion_id = serializer.validated_data.get('discussion_id')
            recipient_id = serializer.validated_data.get('recipient_id')
            title = serializer.validated_data.get('title')
            content = serializer.validated_data['content']
            user = request.user

            try:
                # VÉRIFICATION DES AUTORISATIONS
                if discussion_id:
                    # Envoi dans une discussion existante
                    discussion = Discussion.objects.get(id=discussion_id)
                    
                    # Vérifier que l'utilisateur fait partie de la discussion
                    if user not in [discussion.participant1, discussion.participant2]:
                        return Response({'error': 'Accès non autorisé à cette discussion.'}, status=403)
                    
                    # Vérifier que c'est une discussion avec admin
                    if not discussion.is_admin_involved():
                        return Response({'error': 'Discussion non autorisée.'}, status=403)

                else:
                    # Création d'une nouvelle discussion
                    if not recipient_id:
                        return Response({'error': 'Destinataire requis pour nouvelle discussion.'}, status=400)
                    
                    recipient = User.objects.get(id=recipient_id)
                    
                    # VÉRIFICATION CRITIQUE : Un des participants doit être admin
                    is_user_admin = user.is_staff or user.is_superuser
                    is_recipient_admin = recipient.is_staff or recipient.is_superuser
                    
                    if not (is_user_admin or is_recipient_admin):
                        return Response({
                            'error': 'Les discussions sont uniquement autorisées avec les administrateurs.'
                        }, status=403)
                    
                    # Déterminer le type de discussion
                    if is_user_admin and not is_recipient_admin:
                        discussion_type = 'seller_admin' if recipient.is_seller else 'buyer_admin'
                        participant1, participant2 = user, recipient
                    else:
                        discussion_type = 'seller_admin' if user.is_seller else 'buyer_admin'
                        participant1, participant2 = recipient, user
                    
                    # Créer ou récupérer la discussion
                    discussion, created = Discussion.objects.get_or_create(
                        participant1=participant1,
                        participant2=participant2,
                        defaults={
                            'discussion_type': discussion_type,
                            'title': title or f"Discussion {discussion_type}"
                        }
                    )

                # Créer le message
                message = Message.objects.create(
                    discussion=discussion,
                    sender=user,
                    content=content
                )

                return Response({
                    'id': message.id,
                    'content': message.content,
                    'created_at': message.created_at,
                    'sender': {
                        'id': message.sender.id,
                        'username': message.sender.username,
                        'is_staff': message.sender.is_staff,
                        'is_superuser': message.sender.is_superuser,
                        'is_seller': message.sender.is_seller
                    },
                    'discussion_id': discussion.id
                }, status=status.HTTP_201_CREATED)

            except (Discussion.DoesNotExist, User.DoesNotExist) as e:
                return Response({'error': 'Discussion ou utilisateur non trouvé.'}, status=404)
                
        return Response(serializer.errors, status=400)


class AdminDiscussionView(APIView):
    """Vue spéciale pour les administrateurs pour gérer les discussions"""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        """Lister toutes les discussions pour l'admin"""
        discussions = Discussion.objects.filter(is_active=True).order_by('-updated_at')
        serializer = DiscussionSerializer(discussions, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        """Permettre à l'admin d'initier une discussion avec n'importe qui"""
        serializer = CreateDiscussionSerializer(data=request.data)
        if serializer.is_valid():
            recipient_id = serializer.validated_data['recipient_id']
            title = serializer.validated_data.get('title')
            content = serializer.validated_data['content']
            discussion_type = serializer.validated_data.get('discussion_type', 'support')
            
            try:
                recipient = User.objects.get(id=recipient_id)
                
                discussion, created = Discussion.objects.get_or_create(
                    participant1=request.user,  # Admin
                    participant2=recipient,
                    defaults={
                        'discussion_type': discussion_type,
                        'title': title or f"Discussion {discussion_type}"
                    }
                )
                
                # Créer le premier message
                message = Message.objects.create(
                    discussion=discussion,
                    sender=request.user,
                    content=content
                )
                
                return Response({
                    'discussion_id': discussion.id,
                    'message': 'Discussion créée avec succès',
                    'message_data': MessageSerializer(message).data
                }, status=status.HTTP_201_CREATED)
                
            except User.DoesNotExist:
                return Response({'error': 'Utilisateur non trouvé.'}, status=404)
        
        return Response(serializer.errors, status=400)

    def delete(self, request, discussion_id):
        """Archiver une discussion (soft delete)"""
        try:
            discussion = Discussion.objects.get(id=discussion_id)
            discussion.is_active = False
            discussion.save()
            return Response({'message': 'Discussion archivée avec succès'})
        except Discussion.DoesNotExist:
            return Response({'error': 'Discussion non trouvée'}, status=404)