from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework import viewsets
from django.db.models import F
from google.auth.transport import requests
from google.oauth2 import id_token
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from datetime import timedelta, datetime
from commandes.models import Order
from listings.models import Listing, Category
from transactions.models import Transaction, Revenue
from reviews.models import Review
from reviews.serializers import ReviewSerializer
from listings.serializers import ListingSerializer
from django.db.models import Sum, Count, Avg, Q
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
from .models import User, OneTimePassword, VendorProfile, Address
from .serializers import (UserSerializer,LoginSerializer, 
UserProfileSerializer,SetNewPasswordSerializer,
RequestResetPasswordAPISerializer,LogoutSerializer,VendorProfileSerializer, AddressSerializer)
from rest_framework.throttling import AnonRateThrottle
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.http import Http404
import logging
from django.http import JsonResponse
from allauth.socialaccount.models import SocialAccount
import requests
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
        return Response({'message': 'Déconnexion réussie ✅'}, status=status.HTTP_200_OK)




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
logger = logging.getLogger(__name__)

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


class RequestResetPasswordAPIView(GenericAPIView):
    serializer_class = RequestResetPasswordAPISerializer
    permission_classes = [AllowAny]

    def post(self, request):
        logger.debug("🚀 Requête de réinitialisation reçue: %s", request.data)
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        logger.info("✅ Validation réussie, envoi de l'email...")
        
        # ✅ CORRECTION : Appeler save() pour déclencher l'envoi d'email
        serializer.save()
        
        logger.info("✅ Processus de réinitialisation terminé avec succès")
        
        return Response(
            {'message': "Un lien vous a été envoyé à votre boîte email pour réinitialiser votre mot de passe."},
            status=status.HTTP_200_OK
        )


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

        except Exception as e:
            logger.error(f"Erreur validation token: {e}")
            return Response({'message': 'Le token est invalide ou expiré'}, status=status.HTTP_401_UNAUTHORIZED)


class SetNewPassword(GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [AllowAny]

    def patch(self, request):
        logger.info("Réinitialisation de mot de passe", extra={'data': request.data})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Mot de passe modifié avec succès 👍'}, status=status.HTTP_200_OK)


class TestAuthenticationView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'message': 'Authentifié avec succès',
            'user': {
                'id': request.user.id,
                'email': request.user.email
            }
        })

#@csrf_exempt
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        logger.debug("Requête Facebook reçue: %s", request.data)
        access_token = request.data.get('access_token')
        
        if not access_token:
            logger.error("access_token manquant")
            return Response({'error': 'access_token requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Valider le token avec Facebook
            debug_token_url = "https://graph.facebook.com/debug_token"
            params = {
                'input_token': access_token,
                'access_token': f"{settings.SOCIAL_AUTH_FACEBOOK_KEY}|{settings.SOCIAL_AUTH_FACEBOOK_SECRET}"
            }
            
            response = requests.get(debug_token_url, params=params)
            data = response.json()
            
            if 'error' in data or not data.get('data', {}).get('is_valid'):
                logger.error("Token Facebook invalide: %s", data)
                return Response({'error': 'Token Facebook invalide'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 2. Récupérer les infos utilisateur
            user_info_url = "https://graph.facebook.com/me"
            params = {
                'access_token': access_token,
                'fields': 'id,name,email,first_name,last_name,picture.type(large)'
            }
            
            user_response = requests.get(user_info_url, params=params)
            user_data = user_response.json()
            
            if 'error' in user_data:
                logger.error("Erreur récupération infos: %s", user_data)
                return Response({'error': 'Impossible de récupérer les infos utilisateur'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 3. Gérer l'utilisateur
            email = user_data.get('email')
            if not email:
                # Facebook peut ne pas retourner l'email, créer un email temporaire
                email = f"facebook_{user_data['id']}@facebook.com"
            
            # Vérifier si un SocialAccount existe déjà
            try:
                social_account = SocialAccount.objects.get(uid=user_data['id'])
                user = social_account.user
                created = False
            except SocialAccount.DoesNotExist:
                # Vérifier si un utilisateur normal existe avec cet email
                try:
                    user = User.objects.get(email=email)
                    # L'utilisateur existe mais pas de compte social, créer le lien
                    SocialAccount.objects.create(
                        user=user,
                        provider='facebook',
                        uid=user_data['id'],
                        extra_data=user_data
                    )
                    created = False
                except User.DoesNotExist:
                    # Créer un nouvel utilisateur
                    username = email.split('@')[0]
                    user = User.objects.create(
                        email=email,
                        username=username,
                        first_name=user_data.get('first_name', ''),
                        last_name=user_data.get('last_name', ''),
                        is_verified=True,
                        auth_provider='facebook'
                    )
                    
                    # Créer le SocialAccount
                    SocialAccount.objects.create(
                        user=user,
                        provider='facebook',
                        uid=user_data['id'],
                        extra_data=user_data
                    )
                    created = True
            
            # Mettre à jour les informations
            user.auth_provider = 'facebook'
            user.is_verified = True
            user.save()
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'user_id': user.id,
                'is_new_user': created,
                'message': 'Connexion Facebook réussie'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error("Erreur complète Facebook: %s", str(e), exc_info=True)
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


# views.py - Ajoutez ces vues
# Dans views.py - Ajoutez ces vues

class VendorProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupérer le profil vendeur"""
        print(f"🔍 VendorProfileView GET called for user: {request.user.email}")
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            print(f"✅ Found vendor profile: {vendor_profile}")
            serializer = VendorProfileSerializer(vendor_profile)
            return Response(serializer.data)
        except VendorProfile.DoesNotExist:
            print("❌ Vendor profile not found")
            return Response({
                'message': 'Profil vendeur non trouvé',
                'has_profile': False
            }, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        """Créer ou mettre à jour le profil vendeur"""
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            serializer = VendorProfileSerializer(
                vendor_profile, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
        except VendorProfile.DoesNotExist:
            serializer = VendorProfileSerializer(
                data=request.data, 
                context={'request': request}
            )
        
        if serializer.is_valid():
            vendor_profile = serializer.save()
            return Response({
                'message': 'Profil vendeur sauvegardé avec succès',
                'data': VendorProfileSerializer(vendor_profile).data,
                'is_completed': vendor_profile.is_completed
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request):
        """Mettre à jour complètement le profil vendeur"""
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            serializer = VendorProfileSerializer(
                vendor_profile, 
                data=request.data,
                context={'request': request}
            )
            
            if serializer.is_valid():
                vendor_profile = serializer.save()
                return Response({
                    'message': 'Profil vendeur mis à jour avec succès',
                    'data': VendorProfileSerializer(vendor_profile).data,
                    'is_completed': vendor_profile.is_completed
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except VendorProfile.DoesNotExist:
            return Response({
                'error': 'Profil vendeur non trouvé. Créez d\'abord un profil.'
            }, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        """Mettre à jour partiellement le profil vendeur"""
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            serializer = VendorProfileSerializer(
                vendor_profile, 
                data=request.data,
                partial=True,  # ✅ Important pour PATCH
                context={'request': request}
            )
            
            if serializer.is_valid():
                vendor_profile = serializer.save()
                return Response({
                    'message': 'Profil vendeur mis à jour avec succès',
                    'data': VendorProfileSerializer(vendor_profile).data,
                    'is_completed': vendor_profile.is_completed
                }, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except VendorProfile.DoesNotExist:
            return Response({
                'error': 'Profil vendeur non trouvé. Créez d\'abord un profil.'
            }, status=status.HTTP_404_NOT_FOUND)

class VendorCheckSetupView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Vérifier si le vendeur a complété son setup"""
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            serializer = VendorProfileSerializer(vendor_profile)
            return Response({
                'has_profile': True,
                'is_completed': vendor_profile.is_completed,
                'profile': serializer.data
            })
        except VendorProfile.DoesNotExist:
            return Response({
                'has_profile': False,
                'is_completed': False
            })
# views.py - Ajoutez ces vues

class AddressListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupérer toutes les adresses de l'utilisateur"""
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Créer une nouvelle adresse"""
        serializer = AddressSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            address = serializer.save()
            return Response(
                {
                    'message': 'Adresse créée avec succès',
                    'data': AddressSerializer(address).data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        try:
            return Address.objects.get(pk=pk, user=user)
        except Address.DoesNotExist:
            raise Http404
    
    def get(self, request, pk):
        """Récupérer une adresse spécifique"""
        address = self.get_object(pk, request.user)
        serializer = AddressSerializer(address)
        return Response(serializer.data)
    
    def put(self, request, pk):
        """Mettre à jour une adresse complètement"""
        address = self.get_object(pk, request.user)
        serializer = AddressSerializer(
            address,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Adresse mise à jour avec succès',
                    'data': serializer.data
                }
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        """Mettre à jour partiellement une adresse"""
        address = self.get_object(pk, request.user)
        serializer = AddressSerializer(
            address,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Adresse mise à jour avec succès',
                    'data': serializer.data
                }
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """Supprimer une adresse"""
        address = self.get_object(pk, request.user)
        address.delete()
        return Response(
            {'message': 'Adresse supprimée avec succès'},
            status=status.HTTP_204_NO_CONTENT
        )


class SetDefaultAddressView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        """Définir une adresse comme adresse par défaut"""
        try:
            address = Address.objects.get(pk=pk, user=request.user)
            address.is_default = True
            address.save()
            
            return Response(
                {
                    'message': 'Adresse définie comme adresse par défaut',
                    'data': AddressSerializer(address).data
                }
            )
        except Address.DoesNotExist:
            return Response(
                {'error': 'Adresse non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
@api_view(['GET'])
def region_list(request):
    regions = [
        {'value': 'Bamako', 'label': 'Bamako'},
        {'value': 'Kayes', 'label': 'Kayes'},
        {'value': 'Koulikoro', 'label': 'Koulikoro'},
        {'value': 'Sikasso', 'label': 'Sikasso'},
        {'value': 'Ségou', 'label': 'Ségou'},
        {'value': 'Mopti', 'label': 'Mopti'},
        {'value': 'Tombouctou', 'label': 'Tombouctou'},
        {'value': 'Gao', 'label': 'Gao'},
        {'value': 'Kidal', 'label': 'Kidal'},
    ]
    return Response(regions)

class VendorStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Récupérer toutes les statistiques du vendeur"""
        user = request.user
         # 🔥 AJOUT: Logs de débogage
        logger.info(f"📊 Récupération des stats pour le vendeur: {user.email}")
        # Vérifier que l'utilisateur est un vendeur
        if not user.is_seller:
            return Response(
                {'error': 'Accès réservé aux vendeurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Période pour les comparaisons
        today = timezone.now()
        last_30_days = today - timedelta(days=30)
        previous_30_days = last_30_days - timedelta(days=30)
        
        # 🔥 STATISTIQUES DE VENTES
        # Commandes récentes du vendeur
        vendor_orders = Order.objects.filter(listing__user=user)
        
        # Chiffre d'affaires
        current_period_revenue = vendor_orders.filter(
            created_at__gte=last_30_days,
            status='completed'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        previous_period_revenue = vendor_orders.filter(
            created_at__range=[previous_30_days, last_30_days],
            status='completed'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        revenue_change = self._calculate_percentage_change(
            current_period_revenue, previous_period_revenue
        )
        
        # Nombre de ventes
        current_sales_count = vendor_orders.filter(
            created_at__gte=last_30_days,
            status='completed'
        ).count()
        
        previous_sales_count = vendor_orders.filter(
            created_at__range=[previous_30_days, last_30_days],
            status='completed'
        ).count()
        
        sales_change = self._calculate_percentage_change(
            current_sales_count, previous_sales_count
        )
        
        # 🔥 STATISTIQUES DES PRODUITS
        vendor_listings = Listing.objects.filter(user=user)
        logger.info(f"📈 Vendeur a {vendor_listings.count()} annonces")
        from listings.models import ListingView
        total_views = ListingView.objects.filter(listing__user=user).count()
        logger.info(f"👀 Total des vues pour ce vendeur: {total_views}")
        products_stats = {
            'total': vendor_listings.count(),
            'active': vendor_listings.filter(status='active').count(),
            'out_of_stock': vendor_listings.filter(status='out_of_stock').count(),
            'sold_out': vendor_listings.filter(
                Q(quantity_sold__gte=F('quantity')) | 
                Q(quantity=0)
            ).count(),
            'draft': vendor_listings.filter(status='expired').count(),
        }
        
        # 🔥 STATISTIQUES DES COMMANDES
        orders_stats = {
            'total': vendor_orders.count(),
            'pending': vendor_orders.filter(status='pending').count(),
            'confirmed': vendor_orders.filter(status='confirmed').count(),
            'shipped': vendor_orders.filter(status='shipped').count(),
            'completed': vendor_orders.filter(status='completed').count(),
            'cancelled': vendor_orders.filter(status='cancelled').count(),
        }
        
        # 🔥 AVIS CLIENTS
        vendor_reviews = Review.objects.filter(reviewed=user)
        
        reviews_stats = {
            'total': vendor_reviews.count(),
            'average_rating': vendor_reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
            'rating_distribution': self._get_rating_distribution(vendor_reviews),
            'recent_reviews': self._get_recent_reviews_serialized(vendor_reviews)
        }
        
        # 🔥 PERFORMANCE
        performance_stats = {
            'conversion_rate': self._calculate_conversion_rate(vendor_listings, vendor_orders),
            'average_delivery_time': self._calculate_average_delivery_time(vendor_orders),
            'customer_satisfaction': reviews_stats['average_rating'],
        }
        
        # 🔥 REVENUS ET PORTEFEUILLE
        wallet_stats = {
            'available_balance': self._get_available_balance(user),
            'pending_payouts': self._get_pending_payouts(user),
            'total_earnings': self._get_total_earnings(user),
            'commission_paid': self._get_total_commissions(user),
        }
        
        # 🔥 DONNÉES POUR GRAPHIQUES
        chart_data = {
            'revenue_trend': self._get_revenue_trend(user, 30),
            'sales_trend': self._get_sales_trend(user, 30),
            'top_products': self._get_top_products(user, 5),
        }
        visitor_stats = self._get_visitor_stats(user)
        popular_listings = self._get_popular_listings(user)
        category_stats = self._get_category_stats(user)
        return Response({
            'overview': {
                'revenue': {
                    'current': current_period_revenue,
                    'previous': previous_period_revenue,
                    'change': revenue_change,
                    'currency': 'XOF'
                },
                'sales_count': {
                    'current': current_sales_count,
                    'previous': previous_sales_count,
                    'change': sales_change
                }
            },
            'products': products_stats,
            'orders': orders_stats,
            'reviews': reviews_stats,
            'performance': performance_stats,
            'wallet': wallet_stats,
            'charts': chart_data,
            'visitors': visitor_stats,
            'popular_listings': popular_listings,
            'category_analytics': category_stats,
            'last_updated': timezone.now()
        })
    def _get_recent_reviews_serialized(self, reviews):
        """Sérialiser les avis récents"""
        try:
            from reviews.serializers import ReviewSerializer
            return ReviewSerializer(
                reviews.order_by('-created_at')[:5], 
                many=True
            ).data
        except:
            return []
    
    def _calculate_percentage_change(self, current, previous):
        """Calculer le pourcentage de changement"""
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)
    
    def _get_rating_distribution(self, reviews):
        """Distribution des notes"""
        distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        for review in reviews:
            if review.rating in distribution:
                distribution[review.rating] += 1
        return distribution
    
    def _calculate_conversion_rate(self, listings, orders):
        """Calculer le taux de conversion"""
        # Si vous n'avez pas de compteur de vues, utilisez une estimation
        total_listings = listings.count()
        total_orders = orders.count()
        
        if total_listings == 0:
            return 0
        
        # Estimation basée sur le nombre de produits vs commandes
        return round((total_orders / total_listings) * 100, 2)
    
    def _calculate_average_delivery_time(self, orders):
        """Calculer le délai moyen de livraison"""
        completed_orders = orders.filter(status='completed')
        if not completed_orders.exists():
            return 0
        
        total_days = 0
        count = 0
        
        for order in completed_orders:
            if order.created_at and hasattr(order, 'delivered_at') and order.delivered_at:
                delivery_time = (order.delivered_at - order.created_at).days
                total_days += delivery_time
                count += 1
        
        return round(total_days / count, 1) if count > 0 else 0
    
    def _get_available_balance(self, user):
        """Solde disponible pour retrait"""
        try:
            completed_transactions = Transaction.objects.filter(
                order__listing__user=user,
                status='success'
            )
            return completed_transactions.aggregate(total=Sum('net_amount'))['total'] or 0
        except:
            return 0
    
    def _get_pending_payouts(self, user):
        """Paiements en attente"""
        try:
            pending_orders = Order.objects.filter(
                listing__user=user,
                status='completed'
            ).exclude(transaction__status='success')
            return pending_orders.aggregate(total=Sum('total_price'))['total'] or 0
        except:
            return 0
    
    def _get_total_earnings(self, user):
        """Revenus totaux"""
        try:
            revenues = Revenue.objects.filter(seller=user)
            return revenues.aggregate(total=Sum('amount'))['total'] or 0
        except:
            return 0
    
    def _get_total_commissions(self, user):
        """Commissions totales payées"""
        try:
            transactions = Transaction.objects.filter(order__listing__user=user)
            return transactions.aggregate(total=Sum('commission'))['total'] or 0
        except:
            return 0
    
    def _get_revenue_trend(self, user, days=30):
        """Tendance des revenus sur X jours"""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            daily_revenue = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                next_date = date + timedelta(days=1)
                
                revenue = Order.objects.filter(
                    listing__user=user,
                    status='completed',
                    created_at__range=[date, next_date]
                ).aggregate(total=Sum('total_price'))['total'] or 0
                
                daily_revenue.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'revenue': float(revenue)
                })
            
            return daily_revenue
        except:
            return []
    
    def _get_sales_trend(self, user, days=30):
        """Tendance des ventes sur X jours"""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            daily_sales = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                next_date = date + timedelta(days=1)
                
                sales_count = Order.objects.filter(
                    listing__user=user,
                    status='completed',
                    created_at__range=[date, next_date]
                ).count()
                
                daily_sales.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'sales': sales_count
                })
            
            return daily_sales
        except:
            return []
    
    def _get_top_products(self, user, limit=5):
        """Produits les plus vendus"""
        try:
            from django.db.models import Count
            
            top_products = Listing.objects.filter(
                user=user
            ).annotate(
                total_orders=Count('orders')
            ).order_by('-total_orders')[:limit]
            
            # Serializer basique si le ListingSerializer n'est pas disponible
            return [{
                'id': product.id,
                'title': product.title,
                'price': float(product.price),
                'total_orders': product.total_orders,
                'available_quantity': product.available_quantity
            } for product in top_products]
        except:
            return []
        
        
    def _get_visitor_stats(self, user):
        """Statistiques des visiteurs - VERSION CORRIGÉE"""
        try:
            from listings.models import ListingView
            from django.utils import timezone
            from datetime import timedelta
            
            # IDs des annonces du vendeur
            vendor_listing_ids = Listing.objects.filter(user=user).values_list('id', flat=True)
            
            if not vendor_listing_ids:
                return self._get_empty_visitor_stats()
            
            # Périodes pour la comparaison
            today = timezone.now()
            current_period_start = today - timedelta(days=30)
            previous_period_start = current_period_start - timedelta(days=30)
            previous_period_end = current_period_start
            
            # Vues pour la période actuelle (30 derniers jours)
            current_views = ListingView.objects.filter(
                listing_id__in=vendor_listing_ids,
                viewed_at__gte=current_period_start
            )
            
            # Vues pour la période précédente (30 jours avant)
            previous_views = ListingView.objects.filter(
                listing_id__in=vendor_listing_ids,
                viewed_at__range=[previous_period_start, previous_period_end]
            )
            
            # Calculs réels
            current_total_views = current_views.count()
            current_unique_visitors = current_views.values('ip_address').distinct().count()
            
            previous_total_views = previous_views.count()
            previous_unique_visitors = previous_views.values('ip_address').distinct().count()
            
            # Calcul des pourcentages de changement
            views_change = self._calculate_percentage_change(current_total_views, previous_total_views)
            visitor_change = self._calculate_percentage_change(current_unique_visitors, previous_unique_visitors)
            
            # Vues aujourd'hui
            views_today = ListingView.objects.filter(
                listing_id__in=vendor_listing_ids,
                viewed_at__date=today.date()
            ).count()
            
            return {
                'unique_visitors': {
                    'current': current_unique_visitors,
                    'previous': previous_unique_visitors,
                    'change': visitor_change
                },
                'total_views': {
                    'current': current_total_views,
                    'previous': previous_total_views,
                    'change': views_change
                },
                'views_today': views_today,
                'avg_time_on_site': 2.5  # Vous pouvez implémenter cette logique plus tard
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur stats visiteurs: {str(e)}")
            return self._get_empty_visitor_stats()
            
    #def _get_visitor_stats(self, user):
        """Version temporaire avec données simulées pour testing"""
        # TEMPORAIRE: Simuler des données
        import random
        return {
            'unique_visitors': {
                'current': random.randint(50, 200),
                'previous': random.randint(40, 180),
                'change': random.randint(-20, 50)
            },
            'total_views': {
                'current': random.randint(100, 500),
                'previous': random.randint(80, 450),
                'change': random.randint(-15, 40)
            },
            'views_today': random.randint(5, 25),
            'avg_time_on_site': round(random.uniform(1.5, 4.5), 1)
        }       

    
    def _get_empty_visitor_stats(self):
        """Retourne des stats vides en cas d'erreur"""
        return {
            'unique_visitors': {'current': 0, 'previous': 0, 'change': 0},
            'total_views': {'current': 0, 'previous': 0, 'change': 0},
            'views_today': 0,
            'avg_time_on_site': 0
        }
    
    def _get_popular_listings(self, user, limit=5):
        """Annonces les plus populaires"""
        try:
            from listings.models import ListingView
            
            popular_listings = Listing.objects.filter(user=user).annotate(
                total_views=Count('views'),
                unique_visitors_count=Count('views__ip_address', distinct=True)
            ).order_by('-total_views')[:limit]
            
            return [{
                'id': listing.id,
                'title': listing.title,
                'price': float(listing.price),
                'total_views': listing.total_views or 0,
                'unique_visitors': listing.unique_visitors_count or 0,
                'conversion_rate': self._calculate_listing_conversion_rate(listing),
                'status': listing.status,
                 # Méthode à implémenter
            } for listing in popular_listings]
            
        except Exception as e:
            logger.error(f"Erreur annonces populaires: {str(e)}")
            return []
    
    def _get_category_stats(self, user):
        """Statistiques par catégorie"""
        try:
            from django.db.models import Count, Sum, F
           
            
            # Catégories les plus vendues
            top_categories = Listing.objects.filter(
                user=user,
                orders__status='completed'
            ).values(
                'category__name',
                'category__id'
            ).annotate(
                total_sales=Count('orders'),
                total_revenue=Sum('orders__total_price'),
                #total_views=Sum('views_count'),
                total_listings=Count('id'),
                listings_with_views=Count('id', filter=Q(views_count__gt=0)) ,
                unique_visitors=Sum('unique_visitors')
            ).order_by('-total_sales')[:10]
            
            # Catégories les plus vues
            most_viewed_categories = Listing.objects.filter(
                user=user
            ).values(
                'category__name',
                'category__id'
            ).annotate(
                total_listings=Count('id'),
                listings_with_views=Count('id', filter=Q(views_count__gt=0)),
                total_orders=Count('orders', filter=Q(orders__status='completed'))
            ).order_by('-listings_with_views')[:10] 
            
            return {
                'top_selling_categories': list(top_categories),
                'most_viewed_categories': list(most_viewed_categories),
               
            }
            
        except Exception as e:
            logger.error(f"Erreur stats catégories: {str(e)}")
            return {
                'top_selling_categories': [],
                'most_viewed_categories': []
            }
    
    def _calculate_listing_conversion_rate(self, listing):
        """Taux de conversion d'une annonce"""
        try:
            orders_count = listing.orders.filter(status='completed').count()
            if listing.views_count > 0:
                return round((orders_count / listing.views_count) * 100, 2)
            return 0
        except:
            return 0
    
    def _get_category_performance_metrics(self, user):
        """Métriques de performance par catégorie"""
        try:
            categories = Category.objects.filter(
                listings__user=user
            ).distinct().annotate(
                total_listings=Count('listings', filter=Q(listings__user=user)),
                active_listings=Count('listings', filter=Q(listings__user=user, listings__status='active')),
                total_sales=Count('listings__orders', filter=Q(listings__user=user, listings__orders__status='completed')),
                total_revenue=Sum('listings__orders__total_price', filter=Q(listings__user=user, listings__orders__status='completed')),
                avg_views=Avg('listings__views_count', filter=Q(listings__user=user))
            )
            
            return [{
                'category_id': cat.id,
                'category_name': cat.name,
                'total_listings': cat.total_listings,
                'active_listings': cat.active_listings,
                'total_sales': cat.total_sales or 0,
                'total_revenue': float(cat.total_revenue or 0),
                'average_views': round(cat.avg_views or 0, 1),
                'performance_score': self._calculate_category_performance_score(cat)
            } for cat in categories]
            
        except Exception as e:
            logger.error(f"Erreur métriques catégories: {str(e)}")
            return []
    
    def _calculate_category_performance_score(self, category):
        """Calculer un score de performance pour la catégorie"""
        try:
            score = 0
            if category.total_sales:
                score += category.total_sales * 10
            if category.total_revenue:
                score += float(category.total_revenue) * 0.01
            if category.avg_views:
                score += category.avg_views * 0.5
            return round(score, 2)
        except:
            return 0
    
    def _calculate_avg_time_on_site(self, user):
        """Calculer le temps moyen sur le site (simulation)"""
        # Pour l'instant, retourner une valeur simulée
        # Dans une implémentation réelle, vous utiliseriez des analytics détaillés
        return 2.5  # minutes

class VendorSalesReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Générer un rapport de ventes personnalisable"""
        user = request.user
        
        if not user.is_seller:
            return Response(
                {'error': 'Accès réservé aux vendeurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Paramètres de filtre
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        period = request.GET.get('period', '30d')
        
        # Appliquer les filtres de date
        orders_queryset = Order.objects.filter(listing__user=user)
        
        if start_date and end_date:
            orders_queryset = orders_queryset.filter(
                created_at__range=[start_date, end_date]
            )
        else:
            # Période par défaut : 30 derniers jours
            default_end = timezone.now()
            default_start = default_end - timedelta(days=30)
            orders_queryset = orders_queryset.filter(
                created_at__range=[default_start, default_end]
            )
        
        # Statistiques détaillées
        report_data = {
            'period': {
                'start': start_date or default_start.isoformat(),
                'end': end_date or default_end.isoformat()
            },
            'summary': {
                'total_orders': orders_queryset.count(),
                'completed_orders': orders_queryset.filter(status='completed').count(),
                'total_revenue': orders_queryset.filter(status='completed').aggregate(
                    total=Sum('total_price')
                )['total'] or 0,
                'average_order_value': orders_queryset.filter(status='completed').aggregate(
                    avg=Avg('total_price')
                )['avg'] or 0,
            },
            'orders_by_status': list(orders_queryset.values('status').annotate(
                count=Count('id')
            )),
            'top_products': self._get_top_products_report(user, orders_queryset),
            'daily_breakdown': self._get_daily_breakdown(orders_queryset)
        }
        
        return Response(report_data)
    
    def _get_top_products_report(self, user, orders_queryset):
        """Produits les plus vendus pour le rapport"""
        try:
            top_products = Listing.objects.filter(
                user=user,
                orders__in=orders_queryset
            ).annotate(
                units_sold=Count('orders'),
                revenue=Sum('orders__total_price')
            ).order_by('-revenue')[:10]
            
            return [{
                'id': product.id,
                'title': product.title,
                'units_sold': product.units_sold,
                'revenue': float(product.revenue or 0),
                'price': float(product.price)
            } for product in top_products]
        except:
            return []
    
    def _get_daily_breakdown(self, orders_queryset):
        """Récupérer la répartition quotidienne"""
        try:
            from django.db.models.functions import TruncDate
            
            daily_data = orders_queryset.filter(status='completed').annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                orders=Count('id'),
                revenue=Sum('total_price')
            ).order_by('date')
            
            return list(daily_data)
        except:
            return []

# users/views.py - Correction de VendorPerformanceView

class VendorPerformanceView(APIView):
    """Vue pour les indicateurs de performance détaillés"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if not user.is_seller:
            return Response(
                {'error': 'Accès réservé aux vendeurs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Périodes de comparaison
        today = timezone.now()  # ✅ CORRECTION : Définir today ici
        periods = {
            'current_month': today.replace(day=1),
            'last_month': (today.replace(day=1) - timedelta(days=1)).replace(day=1),
            'current_quarter': today.replace(month=((today.month-1)//3)*3+1, day=1),
            'last_quarter': (today.replace(month=((today.month-1)//3)*3+1, day=1) - timedelta(days=1)).replace(day=1),
        }
        
        performance_data = {
            'sales_performance': self._get_sales_performance(user, periods, today),  # ✅ Passer today en paramètre
            'product_performance': self._get_product_performance(user),
            'customer_metrics': self._get_customer_metrics(user),
            'financial_metrics': self._get_financial_metrics(user, periods, today),  # ✅ Passer today en paramètre
        }
        
        return Response(performance_data)
    
    def _get_sales_performance(self, user, periods, today):  # ✅ Ajouter today comme paramètre
        """Performance des ventes par période"""
        sales_data = {}
        
        for period_name, start_date in periods.items():
            # ✅ CORRECTION : Utiliser today passé en paramètre
            end_date = today if period_name.startswith('current') else start_date + timedelta(days=32)
            
            orders = Order.objects.filter(
                listing__user=user,
                created_at__range=[start_date, end_date],
                status='completed'
            )
            
            sales_data[period_name] = {
                'total_orders': orders.count(),
                'total_revenue': orders.aggregate(total=Sum('total_price'))['total'] or 0,
                'average_order_value': orders.aggregate(avg=Avg('total_price'))['avg'] or 0,
                'unique_customers': orders.values('buyer').distinct().count(),
            }
        
        return sales_data
    
    def _get_product_performance(self, user):
        """Performance des produits"""
        products = Listing.objects.filter(user=user)
        
        return {
            'total_products': products.count(),
            'products_with_sales': products.filter(orders__isnull=False).distinct().count(),
            'conversion_rate': self._calculate_product_conversion_rate(products),
            'inventory_turnover': self._calculate_inventory_turnover(products),
        }
    
    def _get_customer_metrics(self, user):
        """Métriques clients"""
        orders = Order.objects.filter(listing__user=user, status='completed')
        reviews = Review.objects.filter(listing__user=user)
        
        return {
            'repeat_customers': self._get_repeat_customers_count(orders),
            'customer_satisfaction': reviews.aggregate(avg=Avg('rating'))['avg'] or 0,
            'response_rate': self._calculate_response_rate(reviews),
            'negative_feedback_rate': self._calculate_negative_feedback_rate(reviews),
        }
    
    def _get_financial_metrics(self, user, periods, today):  # ✅ Ajouter today comme paramètre
        """Métriques financières"""
        financial_data = {}
        
        for period_name, start_date in periods.items():
            # ✅ CORRECTION : Utiliser today passé en paramètre
            end_date = today if period_name.startswith('current') else start_date + timedelta(days=32)
            
            transactions = Transaction.objects.filter(
                order__listing__user=user,
                created_at__range=[start_date, end_date],
                status='success'
            )
            
            financial_data[period_name] = {
                'gross_revenue': transactions.aggregate(total=Sum('amount'))['total'] or 0,
                'net_revenue': transactions.aggregate(total=Sum('net_amount'))['total'] or 0,
                'commission_paid': transactions.aggregate(total=Sum('commission'))['total'] or 0,
                'profit_margin': self._calculate_profit_margin(transactions),
            }
        
        return financial_data
    
    def _calculate_product_conversion_rate(self, products):
        """Taux de conversion des produits"""
        # Si vous avez un champ views_count, utilisez-le, sinon estimation
        products_with_views = products.filter(views_count__gt=0) if hasattr(products.first(), 'views_count') else products
        if not products_with_views.exists():
            return 0
        
        if hasattr(products.first(), 'views_count'):
            total_views = sum(product.views_count for product in products_with_views)
        else:
            # Estimation basée sur le nombre de produits
            total_views = products.count() * 100  # Estimation arbitraire
        
        total_orders = sum(product.orders.count() for product in products)
        
        return round((total_orders / total_views) * 100, 2) if total_views > 0 else 0
    
    def _calculate_inventory_turnover(self, products):
        """Rotation des stocks"""
        products_with_sales = products.filter(quantity_sold__gt=0)
        if not products_with_sales.exists():
            return 0
        
        avg_inventory = sum(product.quantity for product in products) / products.count()
        total_sold = sum(product.quantity_sold for product in products_with_sales)
        
        return round(total_sold / avg_inventory, 2) if avg_inventory > 0 else 0
    
    def _get_repeat_customers_count(self, orders):
        """Nombre de clients récurrents"""
        from django.db.models import Count
        customer_orders = orders.values('buyer').annotate(
            order_count=Count('id')
        ).filter(order_count__gt=1)
        
        return customer_orders.count()
    
    def _calculate_response_rate(self, reviews):
        """Taux de réponse aux avis"""
        if not reviews.exists():
            return 0
            
        # Vérifier si le modèle Review a un champ seller_response
        if hasattr(reviews.first(), 'seller_response'):
            responded_reviews = reviews.exclude(seller_response__isnull=True).exclude(seller_response='')
        else:
            # Si le champ n'existe pas, retourner 0
            return 0
            
        return round((responded_reviews.count() / reviews.count()) * 100, 2) if reviews.count() > 0 else 0
    
    def _calculate_negative_feedback_rate(self, reviews):
        """Taux de feedback négatif"""
        if not reviews.exists():
            return 0
            
        negative_reviews = reviews.filter(rating__lte=2)
        return round((negative_reviews.count() / reviews.count()) * 100, 2) if reviews.count() > 0 else 0
    
    def _calculate_profit_margin(self, transactions):
        """Marge bénéficiaire"""
        gross_revenue = transactions.aggregate(total=Sum('amount'))['total'] or 0
        net_revenue = transactions.aggregate(total=Sum('net_amount'))['total'] or 0
        
        return round((net_revenue / gross_revenue) * 100, 2) if gross_revenue > 0 else 0
    
# users/views.py - Statistiques avec accès élargi

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_quick_stats(request):
    """Statistiques rapides pour le vendeur"""
    user = request.user
    
    # 🔥 ACCÈS ÉLARGI: Autoriser si is_seller OU a un profil vendeur
    if not user.is_seller and not hasattr(user, 'vendor_profile'):
        return JsonResponse({
            'error': 'Accès réservé aux vendeurs',
            'detail': 'Créez d\'abord un profil vendeur pour accéder aux statistiques.',
            'solution': 'POST /api/users/vendor/create-profile/ avec {"shop_name": "Votre boutique"}'
        }, status=403)
    
    try:
        # Commandes du vendeur
        vendor_orders = Order.objects.filter(listing__user=user)
        vendor_listings = Listing.objects.filter(user=user)
        from listings.models import ListingView
        from django.utils import timezone
        from datetime import timedelta
        vendor_listing_ids = vendor_listings.values_list('id', flat=True)

        today = timezone.now()
        last_30_days = today - timedelta(days=30)
        
        current_views = ListingView.objects.filter(
            listing_id__in=vendor_listing_ids,
            viewed_at__gte=last_30_days
        )
        
        # Période précédente (30-60 jours)
        previous_period_start = last_30_days - timedelta(days=30)
        previous_views = ListingView.objects.filter(
            listing_id__in=vendor_listing_ids,
            viewed_at__range=[previous_period_start, last_30_days]
        )
        
        # Calculs
        current_total_views = current_views.count()
        current_unique_visitors = current_views.values('ip_address').distinct().count()
        
        previous_total_views = previous_views.count()
        previous_unique_visitors = previous_views.values('ip_address').distinct().count()
        
        # Pourcentages de changement
        def calculate_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100, 2)
        
        views_change = calculate_change(current_total_views, previous_total_views)
        visitor_change = calculate_change(current_unique_visitors, previous_unique_visitors)
        
        # Vues aujourd'hui
        views_today = ListingView.objects.filter(
            listing_id__in=vendor_listing_ids,
            viewed_at__date=today.date()
        ).count()

        # Calcul des statistiques
        stats = {
            'user_status': {
                'is_seller': user.is_seller,
                'has_vendor_profile': hasattr(user, 'vendor_profile'),
                'role': user.role,
                'shop_name': user.vendor_profile.shop_name if hasattr(user, 'vendor_profile') else None
            },
            'orders': {
                'total': vendor_orders.count(),
                'pending': vendor_orders.filter(status='pending').count(),
                'confirmed': vendor_orders.filter(status='confirmed').count(),
                'completed': vendor_orders.filter(status='completed').count(),
                'cancelled': vendor_orders.filter(status='cancelled').count(),
            },
            'products': {
                'total': vendor_listings.count(),
                'active': vendor_listings.filter(status='active').count(),
                'out_of_stock': vendor_listings.filter(status='out_of_stock').count(),
                'draft': vendor_listings.filter(status='expired').count(),
            },
            'financial': {
                'total_revenue': float(vendor_orders.filter(status='completed').aggregate(
                    total=Sum('total_price')
                )['total'] or 0),
                'currency': 'XOF'
            },
            'visitors': {
                'unique_visitors': {
                    'current': current_unique_visitors,
                    'previous': previous_unique_visitors,
                    'change': visitor_change
                },
                'total_views': {
                    'current': current_total_views,
                    'previous': previous_total_views,
                    'change': views_change
                },
                'views_today': views_today,
                'avg_time_on_site': 2.5
            }
        
        }
        
        return JsonResponse(stats)
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_vendor_status(request):
    """Vérifier le statut vendeur de l'utilisateur"""
    user = request.user
    
    return Response({
        'user_id': user.id,
        'email': user.email,
        'is_seller': user.is_seller,
        'is_seller_pending': user.is_seller_pending,
        'role': user.role,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'has_vendor_profile': hasattr(user, 'vendor_profile'),
        'vendor_profile_completed': getattr(user.vendor_profile, 'is_completed', False) if hasattr(user, 'vendor_profile') else False
    })
def check_vendor_access(user):
    """Vérifier l'accès vendeur de manière plus flexible"""
    # Si l'utilisateur a explicitement is_seller = True
    if user.is_seller:
        return True
    
    # Si l'utilisateur a un profil vendeur complété
    if hasattr(user, 'vendor_profile') and user.vendor_profile.is_completed:
        return True
    
    # Si l'utilisateur a le rôle 'seller'
    if user.role == 'seller':
        return True
    
    # Si l'utilisateur a des produits en vente
    from listings.models import Listing
    if Listing.objects.filter(user=user).exists():
        return True
    
    return False

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_vendor_status(request):
    """Activer le statut vendeur pour l'utilisateur"""
    user = request.user
    
    # Vérifier si l'utilisateur a un profil vendeur
    if not hasattr(user, 'vendor_profile'):
        return Response(
            {'error': 'Vous devez d\'abord compléter votre profil vendeur.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Vérifier si le profil vendeur est complété
    if not user.vendor_profile.is_completed:
        return Response(
            {'error': 'Votre profil vendeur n\'est pas complété.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Activer le statut vendeur
    user.is_seller = True
    user.is_seller_pending = False
    user.role = 'seller'
    user.save()
    
    return Response({
        'message': 'Statut vendeur activé avec succès!',
        'is_seller': user.is_seller,
        'role': user.role
    })
# users/views.py - Ajoutez cette vue

# users/views.py - Correction complète

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_vendor_profile(request):
    """Créer un profil vendeur pour l'utilisateur"""
    user = request.user
    
    # Vérifier si un profil existe déjà
    if hasattr(user, 'vendor_profile'):
        return Response(
            {'error': 'Un profil vendeur existe déjà.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # 🔥 CORRECTION: Construire le nom complet manuellement
        full_name = f"{user.first_name} {user.last_name}".strip()
        if not full_name:  # Si vide, utiliser le username
            full_name = user.username or user.email.split('@')[0]
        
        # Récupérer le shop_name depuis les données de la requête
        shop_name = request.data.get('shop_name')
        if not shop_name:
            return Response(
                {'error': 'Le nom de la boutique (shop_name) est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Données pour créer un profil vendeur
        profile_data = {
            'user': user,
            'shop_name': shop_name,
            'contact_name': full_name,
            'contact_email': user.email,
            'contact_phone': user.phone or '',
            'account_type': request.data.get('account_type', 'individual'),
        }
        
        # Créer le profil vendeur
        vendor_profile = VendorProfile.objects.create(**profile_data)
        
        return Response({
            'message': 'Profil vendeur créé avec succès!',
            'profile_id': vendor_profile.id,
            'shop_name': vendor_profile.shop_name,
            'contact_name': vendor_profile.contact_name,
            'is_completed': vendor_profile.is_completed,
            'next_step': 'Complétez votre profil vendeur via /api/users/vendor/profile/'
        })
        
    except Exception as e:
        import traceback
        print(f"❌ Erreur création profil vendeur: {str(e)}")
        print(traceback.format_exc())
        return Response(
            {'error': f'Erreur lors de la création du profil: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
# users/views.py - Vérification des données utilisateur

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_user_info(request):
    """Debug: Afficher les informations de l'utilisateur"""
    user = request.user
    
    user_data = {
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.full_name,
        'phone': user.phone,
        'has_full_name_method': hasattr(user, 'get_full_name'),
        'has_full_name_field': hasattr(user, 'full_name'),
    }
    
    # Tester get_full_name si elle existe
    if hasattr(user, 'get_full_name') and callable(user.get_full_name):
        try:
            user_data['get_full_name_result'] = user.get_full_name()
        except Exception as e:
            user_data['get_full_name_error'] = str(e)
    
    return Response(user_data)

class AdminUserViewSet(viewsets.ModelViewSet):
    """Vue d'administration pour les utilisateurs"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # Filtres
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search)
            )
            
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des utilisateurs"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        sellers_count = User.objects.filter(role='seller', is_active=True).count()
        
        # Nouveaux utilisateurs aujourd'hui
        today = timezone.now().date()
        new_users_today = User.objects.filter(created_at__date=today).count()
        
        # Distribution par rôle
        role_distribution = User.objects.values('role').annotate(
            count=Count('id')
        )
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'sellers_count': sellers_count,
            'new_users_today': new_users_today,
            'role_distribution': {
                item['role']: item['count'] for item in role_distribution
            }
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Réinitialiser le mot de passe d'un utilisateur"""
        user = self.get_object()
        # Votre logique de réinitialisation de mot de passe
        # Par exemple, envoyer un email avec un lien de réinitialisation
        return Response({'message': 'Email de réinitialisation envoyé'})
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Exporter les utilisateurs en CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="utilisateurs_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Email', 'Nom', 'Prénom', 'Rôle', 'Téléphone', 'Statut', 'Date d\'inscription'])
        
        users = self.get_queryset()
        for user in users:
            writer.writerow([
                user.email,
                user.last_name,
                user.first_name,
                user.get_role_display(),
                f"{user.country_code}{user.phone}",
                "Actif" if user.is_active else "Inactif",
                user.created_at.strftime('%Y-%m-%d')
            ])
        
        return response

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_users_list(request):
    """Liste des utilisateurs pour l'administration"""
    from .models import User
    from .serializers import UserSerializer
    
    users = User.objects.all()
    
    # Filtres
    role = request.GET.get('role')
    if role:
        users = users.filter(role=role)
        
    search = request.GET.get('search')
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search)
        )
    
    is_active = request.GET.get('is_active')
    if is_active is not None:
        users = users.filter(is_active=is_active.lower() == 'true')
    
    users = users.order_by('-created_at')
    page = int(request.GET.get('page', '1'))
    page_size = int(request.GET.get('page_size', '50'))
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    paginated_users = users[start_index:end_index]
    serializer = UserSerializer(paginated_users, many=True)
    
    data = {
        'count': users.count(),
        'page': page,
        'page_size': page_size,
        'results': serializer.data
    }
    
    # 🔥 CORRECTION: Retourner une Response DRF qui gère automatiquement le JSON
    return Response(data)
@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def admin_update_user(request, user_id):
    """Mettre à jour un utilisateur"""
    try:
        user = User.objects.get(id=user_id)
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Utilisateur non trouvé'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_users_stats(request):
    """Statistiques des utilisateurs pour l'administration"""
    from .models import User
    
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    sellers_count = User.objects.filter(role='seller', is_active=True).count()
    
    # Nouveaux utilisateurs aujourd'hui
    today = timezone.now().date()
    new_users_today = User.objects.filter(created_at__date=today).count()
    
    # Distribution par rôle
    role_distribution = {
        'buyer': User.objects.filter(role='buyer').count(),
        'seller': User.objects.filter(role='seller').count(),
        'admin': User.objects.filter(role='admin').count(),
    }
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'sellers_count': sellers_count,
        'new_users_today': new_users_today,
        'role_distribution': role_distribution
    }
    
    # 🔥 CORRECTION: Retourner une Response DRF
    return Response(stats)

# users/views.py - AJOUT
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_listing_permission(request):
    """Vérifie si l'utilisateur peut créer des annonces"""
    user = request.user
    
    can_create = user.can_create_listing()
    reasons = []
    
    if not can_create:
        if user.role != 'seller':
            reasons.append("Votre rôle n'est pas 'vendeur'")
        elif user.is_seller_pending:
            reasons.append("Votre compte vendeur est en attente de validation")
        elif not user.is_seller:
            reasons.append("Votre compte vendeur n'est pas activé")
    
    return Response({
        'can_create_listings': can_create,
        'user_role': user.role,
        'is_seller': user.is_seller,
        'is_seller_pending': user.is_seller_pending,
        'reasons': reasons,
        'next_actions': [
            "Complétez votre profil vendeur" if user.role == 'seller' and user.is_seller_pending else None,
            "Contactez l'administration pour activer votre compte vendeur" if user.role == 'seller' and not user.is_seller else None
        ]
    })

# Dans users/views.py - AJOUTEZ cette méthode

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_visitor_stats(request):
    """Endpoint de débogage pour les statistiques visiteurs"""
    user = request.user
    
    from listings.models import ListingView, Listing
    from django.utils import timezone
    from datetime import timedelta
    
    vendor_listing_ids = Listing.objects.filter(user=user).values_list('id', flat=True)
    
    debug_info = {
        'vendor_listings_count': len(vendor_listing_ids),
        'vendor_listing_ids': list(vendor_listing_ids),
        'total_listing_views': ListingView.objects.filter(listing_id__in=vendor_listing_ids).count(),
        'unique_ips_total': ListingView.objects.filter(listing_id__in=vendor_listing_ids).values('ip_address').distinct().count(),
    }
    
    # Détails par annonce
    listing_details = []
    for listing_id in vendor_listing_ids:
        listing = Listing.objects.get(id=listing_id)
        views_count = ListingView.objects.filter(listing_id=listing_id).count()
        unique_ips = ListingView.objects.filter(listing_id=listing_id).values('ip_address').distinct().count()
        
        listing_details.append({
            'id': listing_id,
            'title': listing.title,
            'listing_views_count': listing.views_count,  # Depuis le modèle Listing
            'listing_unique_visitors': listing.unique_visitors,  # Depuis le modèle Listing
            'detailed_views_count': views_count,  # Depuis ListingView
            'detailed_unique_ips': unique_ips,  # Depuis ListingView
        })
    
    debug_info['listing_details'] = listing_details
    
    return Response(debug_info)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_visitor_data(request):
    """Endpoint de test pour vérifier les données visiteurs"""
    user = request.user
    
    from listings.models import ListingView, Listing
    from datetime import timedelta
    from django.utils import timezone
    
    vendor_listings = Listing.objects.filter(user=user)
    listing_ids = list(vendor_listings.values_list('id', flat=True))
    
    # Données des 7 derniers jours
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_views = ListingView.objects.filter(
        listing_id__in=listing_ids,
        viewed_at__gte=seven_days_ago
    )
    
    test_data = {
        'vendor_listings_count': len(listing_ids),
        'listing_ids': listing_ids,
        'recent_views_count': recent_views.count(),
        'recent_unique_visitors': recent_views.values('ip_address').distinct().count(),
        'views_by_listing': [],
        'recent_views_detailed': list(recent_views.values('listing_id', 'ip_address', 'viewed_at')[:10])
    }
    
    for listing in vendor_listings:
        listing_views = recent_views.filter(listing_id=listing.id)
        test_data['views_by_listing'].append({
            'listing_id': listing.id,
            'title': listing.title,
            'views_count': listing_views.count(),
            'unique_visitors': listing_views.values('ip_address').distinct().count()
        })
    
    return Response(test_data)
# Dans users/views.py - AJOUTEZ cette vue
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_dashboard_view(request):
    """Tracker la vue du dashboard vendeur"""
    user = request.user
    
    try:
        # Incrémenter un compteur de vues dashboard
        # Vous pouvez créer un modèle DashboardView si nécessaire
        from django.core.cache import cache
        cache_key = f"vendor_dashboard_views_{user.id}"
        current_views = cache.get(cache_key, 0)
        cache.set(cache_key, current_views + 1, 60*60*24) # Cache pour 24h
        
        logger.info(f"📊 Dashboard view tracked for vendor {user.email}")
        
        return Response({
            'message': 'Dashboard view tracked',
            'total_dashboard_views': current_views + 1
        })
        
    except Exception as e:
        logger.error(f"Error tracking dashboard view: {str(e)}")
        return Response({'error': str(e)}, status=500)

# users/views.py - AJOUTEZ CES VUES
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard_stats(request):
    """Statistiques complètes pour le dashboard admin"""
    from django.utils import timezone
    from datetime import timedelta
    from listings.models import Listing
    from commandes.models import Order
    from transactions.models import Transaction
    
    today = timezone.now()
    last_30_days = today - timedelta(days=30)
    
    # Utilisateurs
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    sellers_count = User.objects.filter(role='seller', is_active=True).count()
    new_users_today = User.objects.filter(created_at__date=today.date()).count()
    
    # Produits
    products_count = Listing.objects.filter(status='active').count()
    
    # Commandes et revenus
    recent_orders_count = Order.objects.filter(created_at__gte=last_30_days).count()
    total_revenue = Transaction.objects.filter(
        status='success',
        created_at__gte=last_30_days
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Distribution par rôle
    role_distribution = {
        'buyer': User.objects.filter(role='buyer').count(),
        'seller': User.objects.filter(role='seller').count(),
        'admin': User.objects.filter(role='admin').count(),
    }
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'sellers_count': sellers_count,
        'new_users_today': new_users_today,
        'products_count': products_count,
        'recent_orders_count': recent_orders_count,
        'total_revenue': float(total_revenue),
        'role_distribution': role_distribution,
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_recent_orders(request):
    """Commandes récentes pour le dashboard"""
    from commandes.models import Order
    from commandes.serializers import OrderSerializer
    
    recent_orders = Order.objects.select_related(
        'buyer', 'listing'
    ).order_by('-created_at')[:10]
    
    # Transformation des données pour le frontend
    orders_data = []
    for order in recent_orders:
        orders_data.append({
            'id': f"#{order.id}",
            'customer': f"{order.buyer.first_name} {order.buyer.last_name}",
            'product': order.listing.title,
            'amount': f"€{order.total_price}",
            'status': order.get_status_display(),
            'date': format_relative_time(order.created_at)
        })
    
    return Response(orders_data)

# users/views.py - CORRECTION de admin_top_vendors
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_top_vendors(request):
    """Top vendeurs pour le dashboard - VERSION CORRIGÉE"""
    try:
        from django.db.models import Count, Sum, Avg
        from reviews.models import Review
        
        # CORRECTION: Vérifier que l'utilisateur a des annonces
        top_vendors = User.objects.filter(
            role='seller',
            is_active=True,
            listings__isnull=False  # S'assurer que le vendeur a des annonces
        ).annotate(
            total_orders=Count('listings__orders', distinct=True),
            total_sales=Sum('listings__orders__total_price'),
            avg_rating=Avg('received_reviews__rating')
        ).filter(
            total_orders__gt=0
        ).order_by('-total_sales')[:5]
        
        vendors_data = []
        for vendor in top_vendors:
            vendor_name = "Vendeur sans nom"
            
            # CORRECTION: Gestion sécurisée du nom
            if hasattr(vendor, 'vendor_profile') and vendor.vendor_profile:
                vendor_name = vendor.vendor_profile.shop_name
            elif vendor.get_full_name():
                vendor_name = vendor.get_full_name()
            else:
                vendor_name = vendor.email.split('@')[0]
            
            vendors_data.append({
                'name': vendor_name,
                'sales': float(vendor.total_sales or 0),
                'orders': vendor.total_orders or 0,
                'rating': round(vendor.avg_rating or 4.5, 1)
            })
        
        return Response(vendors_data)
        
    except Exception as e:
        logger.error(f"❌ Erreur dans admin_top_vendors: {str(e)}")
        return Response(
            {'error': 'Erreur lors du chargement des top vendeurs'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
@api_view(['GET'])
@permission_classes([IsAdminUser])
def debug_user_relations(request):
    """Debug: Afficher toutes les relations du modèle User"""
    from django.db.models.fields.related import ForeignKey, ManyToManyField
    
    user_fields = []
    for field in User._meta.get_fields():
        field_info = {
            'name': field.name,
            'type': field.__class__.__name__,
            'related_model': getattr(field, 'related_model', None),
            'is_relation': field.is_relation,
        }
        user_fields.append(field_info)
    
    return Response({
        'user_relations': user_fields,
        'available_choices': [f.name for f in User._meta.get_fields() if f.is_relation]
    })

# users/views.py - AJOUTEZ CETTE VUE
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_recent_orders(request):
    """Commandes récentes pour le dashboard admin"""
    try:
        from commandes.models import Order
        from commandes.serializers import OrderSerializer
        
        # Récupérer les 10 dernières commandes
        recent_orders = Order.objects.select_related(
            'buyer', 'listing'
        ).order_by('-created_at')[:10]
        
        # Transformer les données pour le frontend
        orders_data = []
        for order in recent_orders:
            customer_name = "Client sans nom"
            if order.buyer.get_full_name():
                customer_name = order.buyer.get_full_name()
            elif order.buyer.first_name:
                customer_name = order.buyer.first_name
            else:
                customer_name = order.buyer.email.split('@')[0]
            
            orders_data.append({
                'id': f"#{order.id}",
                'customer': customer_name,
                'product': order.listing.title if order.listing else "Produit supprimé",
                'amount': f"€{order.total_price:.2f}",
                'status': order.get_status_display(),
                'date': format_relative_time(order.created_at)
            })
        
        return Response(orders_data)
        
    except Exception as e:
        logger.error(f"❌ Erreur dans admin_recent_orders: {str(e)}")
        return Response(
            {'error': 'Erreur lors du chargement des commandes récentes'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def format_relative_time(date):
    """Formater la date en temps relatif"""
    from django.utils import timezone
    from django.utils.timesince import timesince
    
    now = timezone.now()
    if date.date() == now.date():
        return f"Il y a {timesince(date, now).split(',')[0]}"
    return date.strftime('%d/%m/%Y')
def get_vendor_display_name(vendor):
    """Get the best display name for a vendor"""
    if hasattr(vendor, 'vendor_profile') and vendor.vendor_profile.shop_name:
        return vendor.vendor_profile.shop_name
    elif vendor.get_full_name():
        return vendor.get_full_name()
    else:
        return vendor.email.split('@')[0]  # Use username part of email


def format_relative_time(date):
    """Formater la date en temps relatif"""
    from django.utils import timezone
    from django.utils.timesince import timesince
    
    now = timezone.now()
    if date.date() == now.date():
        return f"Il y a {timesince(date, now).split(',')[0]}"
    return date.strftime('%d/%m/%Y')

# users/views.py - AJOUTEZ CETTE VUE
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_admin_permission(request):
    """Vérifier si l'utilisateur a les permissions admin"""
    user = request.user
    
    is_admin = (
        user.role == 'admin' or 
        user.is_staff or 
        user.is_superuser or
        user.email.endswith('@e-sugu.com')  # Emails admin spécifiques
    )
    
    return Response({
        'is_admin': is_admin,
        'user': {
            'id': user.id,
            'email': user.email,
            'role': user.role,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
        }
    })

# users/views.py - AJOUTEZ CES VUES MANQUANTES

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_dashboard_stats(request):
    """Statistiques complètes pour le dashboard admin"""
    from django.utils import timezone
    from datetime import timedelta
    from listings.models import Listing
    from commandes.models import Order
    from transactions.models import Transaction
    
    today = timezone.now()
    last_30_days = today - timedelta(days=30)
    
    # Utilisateurs
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    sellers_count = User.objects.filter(role='seller', is_active=True).count()
    new_users_today = User.objects.filter(created_at__date=today.date()).count()
    
    # Produits
    products_count = Listing.objects.filter(status='active').count()
    
    # Commandes et revenus
    recent_orders_count = Order.objects.filter(created_at__gte=last_30_days).count()
    total_revenue = Transaction.objects.filter(
        status='success',
        created_at__gte=last_30_days
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Distribution par rôle
    role_distribution = {
        'buyer': User.objects.filter(role='buyer').count(),
        'seller': User.objects.filter(role='seller').count(),
        'admin': User.objects.filter(role='admin').count(),
    }
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'sellers_count': sellers_count,
        'new_users_today': new_users_today,
        'products_count': products_count,
        'recent_orders_count': recent_orders_count,
        'total_revenue': float(total_revenue),
        'role_distribution': role_distribution,
    }
    
    return Response(stats)

# Dans users/views.py
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_test_endpoint(request):
    """Test endpoint pour vérifier les permissions admin"""
    return Response({
        'message': 'Accès admin autorisé',
        'user': {
            'id': request.user.id,
            'email': request.user.email,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
            'role': request.user.role,
        },
        'has_permission': True
    })