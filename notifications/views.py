# notifications/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .models import Notification
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from .serializers import NotificationSerializer
from rest_framework.permissions import AllowAny
from .serializers import NotificationSerializer, AdminNotificationSerializer
import logging
logger = logging.getLogger(__name__)
class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        try:
            notification = Notification.objects.get(id=id, user=request.user)
            notification.is_read = True
            notification.save()
            serializer = NotificationSerializer(notification)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification non trouvée'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id):
        try:
            notification = Notification.objects.get(id=id, user=request.user)
            notification.delete()
            return Response({'message': 'Notification supprimée'}, status=status.HTTP_204_NO_CONTENT)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification non trouvée'}, status=status.HTTP_404_NOT_FOUND)

class AdminNotificationPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class AdminNotificationView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = AdminNotificationPagination
    
    def get(self, request):
        """Récupérer toutes les notifications admin"""
        try:
            # Filtrer pour les admins (admin_only=True ou notifications système importantes)
            notifications = Notification.objects.filter(
                 Q(admin_only=True) | Q(user__isnull=False)
            ).order_by('-created_at')
            
            # Appliquer les filtres
            status_filter = request.GET.get('status')
            if status_filter == 'unread':
                notifications = notifications.filter(is_read=False)
            elif status_filter == 'read':
                notifications = notifications.filter(is_read=True)
            elif status_filter == 'handled':
                notifications = notifications.filter(is_handled=True)
            elif status_filter == 'pending':
                notifications = notifications.filter(is_handled=False)
            
            type_filter = request.GET.get('type')
            if type_filter:
                notifications = notifications.filter(type=type_filter)
            
            priority_filter = request.GET.get('priority')
            if priority_filter:
                notifications = notifications.filter(priority=priority_filter)
            
            # Recherche
            search = request.GET.get('search')
            if search:
                notifications = notifications.filter(
                    Q(content__icontains=search) |
                    Q(data__icontains=search)
                )
            
            # Pagination
            paginator = self.pagination_class()
            result_page = paginator.paginate_queryset(notifications, request)
            serializer = AdminNotificationSerializer(result_page, many=True)
            
            # Statistiques
            stats = {
                'total': notifications.count(),
                'unread': notifications.filter(is_read=False).count(),
                'unhandled': notifications.filter(is_handled=False).count(),
                'urgent': notifications.filter(priority='urgent', is_handled=False).count(),
                'by_type': notifications.values('type').annotate(count=Count('id')),
                'by_priority': notifications.values('priority').annotate(count=Count('id')),
            }
            
            return Response({
                'results': serializer.data,
                'pagination': {
                    'count': paginator.page.paginator.count,
                    'next': paginator.get_next_link(),
                    'previous': paginator.get_previous_link(),
                },
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Erreur récupération notifications admin: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la récupération des notifications'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Créer une notification admin"""
        try:
            data = request.data.copy()
            data['admin_only'] = True  # Toujours admin_only pour les créations admin
            data['created_by'] = request.user.id
            
            serializer = AdminNotificationSerializer(data=data)
            if serializer.is_valid():
                notification = serializer.save()
                
                # Log de création
                logger.info(
                    f"Notification admin créée par {request.user.email}",
                    extra={
                        'notification_id': notification.id,
                        'type': notification.type,
                        'priority': notification.priority,
                        'admin_id': request.user.id
                    }
                )
                
                return Response({
                    'message': 'Notification créée avec succès',
                    'notification': AdminNotificationSerializer(notification).data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur création notification admin: {str(e)}")
            return Response(
                {'error': 'Erreur lors de la création de la notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminNotificationDetailView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request, id):
        """Récupérer une notification spécifique"""
        try:
            notification = Notification.objects.get(id=id)
            
            # Marquer comme lue si ce n'est pas encore le cas
            if not notification.is_read:
                notification.is_read = True
                notification.save()
            
            serializer = AdminNotificationSerializer(notification)
            return Response(serializer.data)
            
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, id):
        """Mettre à jour une notification (marquer comme lue/traitée)"""
        try:
            notification = Notification.objects.get(id=id)
            
            # Vérifier si on marque comme traitée
            if request.data.get('is_handled') == True and not notification.is_handled:
                notification.is_handled = True
                notification.handled_by = request.user
                notification.handled_at = timezone.now()
            
            # Mettre à jour autres champs
            serializer = AdminNotificationSerializer(notification, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                # Log de mise à jour
                if request.data.get('is_handled') == True:
                    logger.info(
                        f"Notification #{id} marquée comme traitée par {request.user.email}",
                        extra={
                            'notification_id': id,
                            'handled_by': request.user.id,
                            'handled_at': timezone.now().isoformat()
                        }
                    )
                
                return Response({
                    'message': 'Notification mise à jour avec succès',
                    'notification': serializer.data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, id):
        """Supprimer une notification"""
        try:
            notification = Notification.objects.get(id=id)
            
            # Log avant suppression
            logger.info(
                f"Notification #{id} supprimée par {request.user.email}",
                extra={
                    'notification_id': id,
                    'deleted_by': request.user.id,
                    'deleted_at': timezone.now().isoformat(),
                    'content': notification.content[:100],
                    'type': notification.type
                }
            )
            
            notification.delete()
            
            return Response(
                {'message': 'Notification supprimée avec succès'},
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )

class AdminNotificationBulkView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """Actions en masse sur les notifications"""
        action = request.data.get('action')
        notification_ids = request.data.get('notification_ids', [])
        
        if not action or not notification_ids:
            return Response(
                {'error': 'Action et notification_ids requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            notifications = Notification.objects.filter(id__in=notification_ids)
            
            if action == 'mark_read':
                updated = notifications.filter(is_read=False).update(
                    is_read=True
                )
                message = f'{updated} notification(s) marquée(s) comme lue(s)'
                
            elif action == 'mark_handled':
                updated = notifications.filter(is_handled=False).update(
                    is_handled=True,
                    handled_by=request.user,
                    handled_at=timezone.now()
                )
                message = f'{updated} notification(s) marquée(s) comme traitée(s)'
                
            elif action == 'delete':
                count = notifications.count()
                
                # Log de suppression en masse
                logger.info(
                    f"{count} notifications supprimées par {request.user.email}",
                    extra={
                        'deleted_by': request.user.id,
                        'deleted_count': count,
                        'notification_ids': notification_ids[:10]  # Limiter la taille du log
                    }
                )
                
                notifications.delete()
                message = f'{count} notification(s) supprimée(s)'
                
            else:
                return Response(
                    {'error': 'Action non valide'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({'message': message})
            
        except Exception as e:
            logger.error(f"Erreur action en masse notifications: {str(e)}")
            return Response(
                {'error': 'Erreur lors de l\'action en masse'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminSendNotificationView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        """Envoyer une notification à des utilisateurs spécifiques"""
        try:
            users = request.data.get('users', [])  # IDs utilisateurs
            user_groups = request.data.get('user_groups', [])  # 'sellers', 'buyers', 'all'
            notification_data = request.data.get('notification', {})
            
            if not notification_data:
                return Response(
                    {'error': 'Données de notification requises'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Déterminer les destinataires
            recipients = []
            
            if 'all' in user_groups:
                from users.models import User
                recipients = list(User.objects.filter(is_active=True).values_list('id', flat=True))
            else:
                if 'sellers' in user_groups:
                    from users.models import User
                    sellers = User.objects.filter(role='seller', is_active=True)
                    recipients.extend(list(sellers.values_list('id', flat=True)))
                
                if 'buyers' in user_groups:
                    from users.models import User
                    buyers = User.objects.filter(role='buyer', is_active=True)
                    recipients.extend(list(buyers.values_list('id', flat=True)))
            
            # Ajouter les utilisateurs spécifiques
            recipients.extend(users)
            recipients = list(set(recipients))  # Supprimer les doublons
            
            if not recipients:
                return Response(
                    {'error': 'Aucun destinataire valide'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Créer les notifications
            created_count = 0
            from users.models import User
            
            for user_id in recipients:
                try:
                    user = User.objects.get(id=user_id)
                    
                    Notification.objects.create(
                        user=user,
                        type=notification_data.get('type', 'system'),
                        content=notification_data.get('content', ''),
                        data=notification_data.get('data', {}),
                        priority=notification_data.get('priority', 'medium'),
                        created_by=request.user
                    )
                    created_count += 1
                    
                except User.DoesNotExist:
                    continue
            
            # Log de l'envoi
            logger.info(
                f"Notifications envoyées par {request.user.email} à {created_count} utilisateurs",
                extra={
                    'sent_by': request.user.id,
                    'recipient_count': created_count,
                    'user_groups': user_groups,
                    'notification_type': notification_data.get('type')
                }
            )
            
            return Response({
                'message': f'{created_count} notification(s) envoyée(s) avec succès',
                'sent_count': created_count,
                'recipients': recipients[:50]  # Limiter la réponse
            })
            
        except Exception as e:
            logger.error(f"Erreur envoi notifications: {str(e)}")
            return Response(
                {'error': 'Erreur lors de l\'envoi des notifications'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminNotificationStatsView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Statistiques des notifications"""
        try:
            from django.db.models import Count, Q
            from django.utils import timezone
            from datetime import timedelta
            
            now = timezone.now()
            last_24h = now - timedelta(hours=24)
            last_7d = now - timedelta(days=7)
            last_30d = now - timedelta(days=30)
            
            stats = {
                'time_periods': {
                    'last_24h': Notification.objects.filter(
                        created_at__gte=last_24h
                    ).count(),
                    'last_7d': Notification.objects.filter(
                        created_at__gte=last_7d
                    ).count(),
                    'last_30d': Notification.objects.filter(
                        created_at__gte=last_30d
                    ).count(),
                },
                'by_type': list(Notification.objects.values('type').annotate(
                    count=Count('id')
                ).order_by('-count')),
                'by_priority': list(Notification.objects.values('priority').annotate(
                    count=Count('id')
                ).order_by('-count')),
                'handling_stats': {
                    'total_handled': Notification.objects.filter(is_handled=True).count(),
                    'avg_handling_time': self._calculate_avg_handling_time(),
                    'pending_by_priority': {
                        'urgent': Notification.objects.filter(
                            priority='urgent', is_handled=False
                        ).count(),
                        'high': Notification.objects.filter(
                            priority='high', is_handled=False
                        ).count(),
                        'medium': Notification.objects.filter(
                            priority='medium', is_handled=False
                        ).count(),
                        'low': Notification.objects.filter(
                            priority='low', is_handled=False
                        ).count(),
                    }
                },
                'admin_stats': {
                    'most_active_admins': list(
                        Notification.objects.filter(
                            handled_by__isnull=False
                        ).values('handled_by__email').annotate(
                            count=Count('id')
                        ).order_by('-count')[:10]
                    ),
                    'notifications_sent_by_admin': list(
                        Notification.objects.filter(
                            created_by__isnull=False
                        ).values('created_by__email').annotate(
                            count=Count('id')
                        ).order_by('-count')[:10]
                    ),
                }
            }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"Erreur statistiques notifications: {str(e)}")
            return Response(
                {'error': 'Erreur lors du calcul des statistiques'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_avg_handling_time(self):
        """Calculer le temps moyen de traitement"""
        from django.db.models import Avg
        from django.db.models.functions import Extract
        from django.db.models import F
        
        handled = Notification.objects.filter(
            is_handled=True,
            handled_at__isnull=False,
            created_at__isnull=False
        )
        
        if not handled.exists():
            return 0
        
        # Calcul en secondes
        avg_seconds = handled.annotate(
            handling_time=Extract(F('handled_at') - F('created_at'), 'epoch')
        ).aggregate(avg=Avg('handling_time'))['avg'] or 0
        
        # Convertir en heures
        return round(avg_seconds / 3600, 2)