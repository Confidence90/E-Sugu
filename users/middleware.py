# users/middleware.py - CRÉEZ CE FICHIER
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
import jwt
from django.conf import settings

User = get_user_model()

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Exclure les URLs qui n'ont pas besoin d'authentification
        public_paths = [
            '/api/users/login/',
            '/api/users/register/',
            '/api/users/verify-otp/',
            '/api/users/password-reset/',
            '/admin/',
            '/api/docs/',
            '/api/schema/',
        ]
        
        if any(request.path.startswith(path) for path in public_paths):
            return None
        
        # Vérifier le token JWT
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'error': 'Token manquant ou invalide'}, 
                status=401
            )
        
        token = auth_header.split(' ')[1]
        
        try:
            # Décoder le token
            payload = AccessToken(token)
            user_id = payload['user_id']
            
            # Récupérer l'utilisateur
            user = User.objects.get(id=user_id)
            request.user = user
            
        except jwt.ExpiredSignatureError:
            return JsonResponse(
                {'error': 'Token expiré'}, 
                status=401
            )
        except jwt.InvalidTokenError:
            return JsonResponse(
                {'error': 'Token invalide'}, 
                status=401
            )
        except User.DoesNotExist:
            return JsonResponse(
                {'error': 'Utilisateur non trouvé'}, 
                status=401
            )
        
        return None