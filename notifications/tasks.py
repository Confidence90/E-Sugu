# notifications/tasks.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from .models import Notification
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Nettoyer les anciennes notifications'
    
    def handle(self, *args, **options):
        try:
            # Supprimer les notifications de plus de 90 jours
            cutoff_date = timezone.now() - timedelta(days=90)
            expired_count = Notification.objects.filter(
                created_at__lt=cutoff_date
            ).count()
            
            Notification.objects.filter(
                created_at__lt=cutoff_date
            ).delete()
            
            # Supprimer les notifications expirées (avec expires_at)
            expired_notifications = Notification.objects.filter(
                expires_at__lt=timezone.now()
            ).count()
            
            Notification.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()
            
            total_deleted = expired_count + expired_notifications
            
            logger.info(
                f"Nettoyage notifications: {total_deleted} notifications supprimées",
                extra={
                    'expired_90d': expired_count,
                    'expired_by_date': expired_notifications,
                    'total_deleted': total_deleted
                }
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Succès: {total_deleted} notifications nettoyées'
                )
            )
            
        except Exception as e:
            logger.error(f"Erreur nettoyage notifications: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Erreur: {str(e)}')
            )