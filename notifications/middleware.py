# notifications/middleware.py
import json
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class NotificationAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Loguer les actions admin sur les notifications
        if request.path.startswith('/api/notifications/admin/') and request.user.is_authenticated:
            if request.method in ['DELETE', 'PATCH', 'POST']:
                self.log_admin_action(request, response)
        
        return response
    
    def log_admin_action(self, request, response):
        """Loguer les actions admin sur les notifications"""
        try:
            log_data = {
                'timestamp': timezone.now().isoformat(),
                'admin_id': request.user.id,
                'admin_email': request.user.email,
                'path': request.path, 
                'method': request.method,
                'status_code': response.status_code,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': request.META.get('REMOTE_ADDR', ''),
            }
            
            if request.method == 'DELETE':
                # Pour DELETE, on a l'ID dans l'URL
                log_data['action'] = 'delete_notification'
                log_data['notification_id'] = request.path.split('/')[-2]
                
            elif request.method == 'PATCH':
                log_data['action'] = 'update_notification'
                log_data['data'] = request.data
                
            elif request.method == 'POST' and '/send/' in request.path:
                log_data['action'] = 'send_notification'
                log_data['data'] = {
                    'recipients_count': response.data.get('sent_count', 0) if hasattr(response, 'data') else 0
                }
            
            logger.info("Action admin notifications", extra=log_data)
            
        except Exception as e:
            logger.error(f"Erreur log middleware notifications: {str(e)}")