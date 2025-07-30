from rest_framework.views import APIView
from google.auth.transport import requests
from google.oauth2 import id_token
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.response import Response
from rest_framework import status, permissions
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.generics import GenericAPIView
from django.conf import settings
from django.shortcuts import redirect
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from rest_framework import serializers
from .utils import assign_otp_to_user, send_otp_email, verify_otp
from rest_framework.parsers import MultiPartParser, FormParser
from .models import User, OneTimePassword
from .serializers import (UserSerializer,LoginSerializer, 
UserProfileSerializer,SetNewPasswordSerializer,
RequestResetPasswordAPISerializer,LogoutSerializer)
from rest_framework.throttling import AnonRateThrottle
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import logging
logger = logging.getLogger(__name__)
# 🚀 Créer un compte utilisateur
#@csrf_exempt
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        is_google_signup = data.get('is_google', False)

        serializer = UserSerializer(data=data)
        logger.debug("Données reçus: %s", data)
        if serializer.is_valid():
            user = serializer.save()

            # Marquage spécifique au vendeur
            if user.is_seller:
                user.is_seller_pending = True
                user.save()

            if is_google_signup:
                # Inscription Google : bypass OTP
                user.is_verified = True
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "message": "Inscription via Google réussie ✅"
                }, status=status.HTTP_201_CREATED)

            else:
                # Inscription classique : OTP requis
                try:
                    otp_code = assign_otp_to_user(user)
                    send_otp_email(user, otp_code)
                except Exception as e:
                    logger.exception("Erreur lors de l’envoi OTP pour l’utilisateur %s", user.email)
                    user.delete()
                    return Response({
                        "error": f"Échec d'envoi du code OTP : {str(e)}"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({
                    "user_id": user.id,
                    "message": "Inscription réussie. Vérifiez votre boîte email pour l’OTP ✉️"
                }, status=status.HTTP_201_CREATED)
        else:
            logger.error("Erreur de validation: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Vérifier le code OTP
#@csrf_exempt
class VerifyUserOTP(GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        otpcode = request.data.get('otp')
        email = request.data.get('email')
        logger.debug("Vérification OTP pour email: %s, code: %s", email, otpcode)
        if not otpcode:
            return Response({'message': 'Code OTP requis'}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({'message': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            otp_obj = OneTimePassword.objects.get(code=otpcode, user__email=email)
            user = otp_obj.user

            is_valid, message = verify_otp(user, otpcode)

            if is_valid:
                user.is_active = True
                user.save()
                otp_obj.delete()
                return Response({'message': 'Email vérifié avec succès.'}, status=status.HTTP_200_OK)

            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)
     
        except OneTimePassword.DoesNotExist:
            return Response({'message': 'Code invalide ou expiré.'}, status=status.HTTP_404_NOT_FOUND)
        


# 🔐 Login
#@csrf_exempt
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]  # Protection contre les attaques brute force

    def post(self, request):
        logger.debug("Requête de connexion: %s ",  request.data)
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        try:
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            user = data["user"]
            
            # Log de la connexion réussie
            logger.info(f"User {user.email} logged in successfully", extra={
                'user_id': user.id,
                'ip': request.META.get('REMOTE_ADDR')
            })
            
            return Response({
                "access": data["access_token"],
                "refresh": data["refresh_token"],
                "email": data["email"],
                'full_name': data["full_name"]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log des échecs de connexion
            logger.warning(f"Login failed for email {request.data.get('email')}: {str(e)}", extra={
                'ip': request.META.get('REMOTE_ADDR')
            })
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# 🚪 Logout

class LogoutView(GenericAPIView):
    serializer_class=LogoutSerializer
    permission_classes=[IsAuthenticated]

    def post(self, request):
        logger.info(f"Déconnexion pour {request.user.email}", extra={'user_id': request.user.id})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Déconnexion réussie ✅'},status=status.HTTP_204_NO_CONTENT)



# 🔁 Rafraîchir le token
#@csrf_exempt
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug("Requête de rafraîchissement: %s", request.data)
        try:
            refresh_token = request.data.get('refresh_token')
            refresh = RefreshToken(refresh_token)
            return Response({
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Token invalide'}, status=status.HTTP_401_UNAUTHORIZED)


# 👤 Consulter & modifier son profil
#@csrf_exempt
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        logger.info(f"Mise à jour profil pour {request.user.email}", extra={'user_id': request.user.id})
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 🔑 Réinitialisation du mot de passe (demande OTP)
#@csrf_exempt
class RequestResetPasswordAPIView(GenericAPIView):
    serializer_class = RequestResetPasswordAPISerializer
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug("Requête de réinitialisation: %s", request.data)
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(
            {'message': "Un lien vous a été envoyé à votre boîte email pour réinitialiser votre mot de passe."},
            status=status.HTTP_200_OK
        )


# 🔒 Réinitialisation du mot de passe (confirmer)
#@csrf_exempt
class ConfirmResetPasswordWithOTPAPIView(GenericAPIView):
    def post(self, request):
        logger.debug("Réinitialisation OTP: %s", request.data)
        identifier = request.data.get('identifier')
        otp_code = request.data.get('otp_code')
        new_password = request.data.get('new_password')

        if not all([identifier, otp_code, new_password]):
            return Response({'error': 'Tous les champs sont requis.'}, status=400)

        try:
            user = User.objects.get(phone_full=identifier) if identifier.startswith('+') else User.objects.get(email=identifier)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=404)

        is_valid, message = verify_otp(user, otp_code)
        if not is_valid:
            return Response({'error': message}, status=400)

        user.set_password(new_password)
        user.save()
        OneTimePassword.objects.filter(user=user, code=otp_code).delete()
        return Response({'message': 'Mot de passe réinitialisé avec succès.'}, status=200)
    
#@csrf_exempt
class ConfirmResetPasswordLinkAPIView(GenericAPIView):
    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response({'message': 'Le token est invalide ou expiré'}, status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                'success': True,
                'message': 'Token valide. Veuillez soumettre votre nouveau mot de passe.',
                'uidb64': uidb64,
                'token': token
            }, status=status.HTTP_200_OK)

        except DjangoUnicodeDecodeError:
            return Response({'message': 'Le token est invalide ou expiré'}, status=status.HTTP_401_UNAUTHORIZED)


# 3. Réinitialisation depuis lien web (POST avec n
# ouveau mot de passe)
#@csrf_exempt
class SetNewPassword(GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [AllowAny]

    def patch(self, request):
        logger.info("Réinitialisation de mot de passe", extra={'data': request.data})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Mot de passe modifié avec succès 👍'}, status=status.HTTP_200_OK)
#@csrf_exempt
class TestAuthenticationView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data={
            'msg':'ça fonctionne!'
        }
        return Response(data, status=status.HTTP_200_OK)
    
logger = logging.getLogger(__name__)
User = get_user_model()

#@csrf_exempt
class GoogleLoginView(APIView):
    def post(self, request, *args, **kwargs):
        logger.debug("Requête reçue: %s", request.data)
        id_token_str = request.data.get('id_token')
        if not id_token_str:
            logger.error("id_token manquant")
            return Response({'error': 'id_token requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Valider l'ID token avec Google
            id_info = id_token.verify_oauth2_token(
                id_token_str, requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            logger.debug("ID token info: %s", id_info)
            
            # Vérifier l'émetteur et l'audience
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return Response({'error': 'Émetteur de jeton non valide'}, status=status.HTTP_400_BAD_REQUEST)
            if id_info['aud'] != settings.GOOGLE_CLIENT_ID:
                return Response({'error': 'Discordance d\'audience'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer ou créer l'utilisateur
            email = id_info['email']
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': id_info.get('given_name', ''),
                    'last_name': id_info.get('family_name', ''),
                    'username': email,
                    'is_verified': True,
                    'auth_provider': 'google'
                }
            )
            if not created:
                user.auth_provider = 'google'
                user.is_verified = True
                user.save()
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'email': email,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        except ValueError as e:
            logger.error("Erreur de validation de l'ID token: %s", str(e))
            return Response({'error': f'Jeton invalide: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
#@csrf_exempt 
class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        
        # Validation de l'email requis
        if not email:
            return Response({"message": "L'email est requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Vérification de l'existence de l'utilisateur par son email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Aucun utilisateur trouvé avec cet email."}, status=status.HTTP_404_NOT_FOUND)

        # Génération d'un nouveau code OTP et assignation à l'utilisateur
        new_code = assign_otp_to_user(user)

        # Envoi du code OTP par email
        send_otp_email(user, new_code)

        return Response({"message": "Un nouveau code OTP a été envoyé à votre adresse email."}, status=status.HTTP_200_OK)
    

#@csrf_exempt
class CustomGoogleCallbackView(OAuth2CallbackView):
    adapter_class = GoogleOAuth2Adapter

    def dispatch(self, request, *args, **kwargs):
        logger.debug("Received callback request: %s", request.GET)
        try:
            response = super().dispatch(request, *args, **kwargs)
            user = request.user
            if user.is_authenticated:
                user.auth_provider = 'google'
                user.is_verified = True
                user.save()

                refresh = RefreshToken.for_user(user)
                redirect_url = (
                    f'http://localhost:5173/auth/callback?'
                    f'access_token={str(refresh.access_token)}&'
                    f'refresh_token={str(refresh)}&'
                    f'email={user.email}'  # Ajouter l'email
                )
                logger.debug("Redirecting to: %s", redirect_url)
                return redirect(redirect_url)
            return response
        except Exception as e:
            logger.error("Error in CustomGoogleCallbackView: %s", str(e))
            return Response({'error': f'Erreur lors du callback: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class FacebookLoginView(APIView):
    def post(self, request, *args, **kwargs):
        logger.debug("Requête reçue: %s", request.data)
        access_token = request.data.get('access_token')
        if not access_token:
            logger.error("access_token manquant")
            return Response({'error': 'access_token requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            adapter = FacebookOAuth2Adapter(request)
            app = adapter.get_provider().get_app(request)
            token = adapter.parse_token({'access_token': access_token})
            token.app = app
            login = adapter.complete_login(request, app, token, response=token)
            login.token = token

            user = login.user
            user.auth_provider = 'facebook'
            user.is_verified = True
            user.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'email': user.email,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        except OAuth2Error as e:
            logger.error("Erreur Facebook OAuth: %s", str(e))
            return Response({'error': f'Erreur de connexion Facebook: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class AppleLoginView(APIView):
    def post(self, request, *args, **kwargs):
        logger.debug("Requête reçue: %s", request.data)
        id_token = request.data.get('id_token')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        if not id_token:
            logger.error("id_token manquant")
            return Response({'error': 'id_token requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            adapter = AppleOAuth2Adapter(request)
            app = adapter.get_provider().get_app(request)
            token = adapter.parse_token({'id_token': id_token})
            token.app = app
            login = adapter.complete_login(request, app, token, response=token)
            login.token = token

            user = login.user
            if first_name and last_name:
                user.first_name = first_name
                user.last_name = last_name
            user.auth_provider = 'apple'
            user.is_verified = True
            user.save()

            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'email': user.email,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        except OAuth2Error as e:
            logger.error("Erreur Apple OAuth: %s", str(e))
            return Response({'error': f'Erreur de connexion Apple: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)