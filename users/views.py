from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from twilio.rest import Client
from .models import User
from .serializers import (
    UserSerializer,
    LoginSerializer,
    UserProfileSerializer
)

# 🚀 Créer un compte utilisateur
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Activer flag KYC vendeur
            if user.is_seller:
                user.is_seller_pending = True

            # En mode dev, activer sans vérification
            if settings.DEBUG:
                user.is_active = True
                user.save()
            else:
                # Envoyer OTP avec Twilio
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                    to=user.phone_full,
                    channel='sms'
                )
            return Response({
                'user_id': user.id,
                'message': 'Code OTP envoyé pour vérification' if not settings.DEBUG else (
                    'Compte actif. KYC en attente.' if user.is_seller else 'Compte créé avec succès.'
                )
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ✅ Vérifier un compte via code OTP
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_full = request.data.get('phone_full')
        otp = request.data.get('otp')
        try:
            user = User.objects.get(phone_full=phone_full)
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            result = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
                to=phone_full, code=otp
            )
            if result.status == 'approved':
                user.is_active = True
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Compte vérifié avec succès',
                    'token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'user_id': user.id
                }, status=status.HTTP_200_OK)
            return Response({'error': 'OTP invalide'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

# 🔐 Login
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 🚪 Logout
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Token invalide'}, status=status.HTTP_400_BAD_REQUEST)

# 🔁 Rafraîchir le token
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            refresh = RefreshToken(refresh_token)
            return Response({
                'token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Token invalide'}, status=status.HTTP_401_UNAUTHORIZED)

# 🔑 Réinitialisation par téléphone
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get('identifier')
        try:
            user = User.objects.get(phone_full=identifier) if identifier.startswith('+') else User.objects.get(email=identifier)
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                to=user.phone_full, channel='sms'
            )
            return Response({'message': 'Code envoyé pour réinitialisation'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Aucun utilisateur trouvé'}, status=status.HTTP_404_NOT_FOUND)

# 👤 Consulter & modifier son profil
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class RequestResetPasswordAPIView(APIView):
    def post(self, request):
        phone = request.data.get('phone_full')
        try:
            user = User.objects.get(phone_full=phone)
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
                to=phone, channel='sms'
            )
            return Response({"message": "Code envoyé avec succès."})
        except User.DoesNotExist:
            return Response({"error": "Utilisateur introuvable."}, status=404)  
class ConfirmResetPasswordAPIView(APIView):
    def post(self, request):
        phone = request.data.get('phone_full')
        code = request.data.get('otp_code')
        new_password = request.data.get('new_password')

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        verification = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verification_checks.create(
            to=phone, code=code
        )
        if verification.status == "approved":
            try:
                user = User.objects.get(phone_full=phone)
                user.set_password(new_password)
                user.save()
                return Response({"message": "Mot de passe réinitialisé avec succès."})
            except User.DoesNotExist:
                return Response({"error": "Utilisateur introuvable."}, status=404)
        return Response({"error": "Code OTP invalide."}, status=400)
