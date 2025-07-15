from rest_framework.views import APIView
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import smart_str, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.generics import GenericAPIView
from django.conf import settings
from rest_framework import serializers
from .utils import assign_otp_to_user, send_otp_email, verify_otp
from rest_framework.parsers import MultiPartParser, FormParser
from .models import User, OneTimePassword
from .serializers import (UserSerializer,LoginSerializer, 
UserProfileSerializer,SetNewPasswordSerializer,
RequestResetPasswordAPISerializer,LogoutSerializer,
GoogleSignInSerializer)

# 🚀 Créer un compte utilisateur
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("Données reçues:", request.data) 
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            try:
                code = assign_otp_to_user(user)
                send_otp_email(user, code)
            except Exception as e:
                user.delete()
                return Response(
                    {'error': f"Échec d'envoi du code OTP. Détail : {str(e)}"},
                    status=500
                )

            if user.is_seller:
                user.is_seller_pending = True  # Assure-toi que ce champ existe dans ton modèle

            

            return Response({
                'user_id': user.id,
                'message': 'Code OTP envoyé pour vérification'
            }, status=status.HTTP_201_CREATED)
        else:
            print("Erreurs de validation:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Vérifier le code OTP
class VerifyUserOTP(GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        otpcode = request.data.get('otp')
        email = request.data.get('email')
        if not otpcode:
            return Response({'message': 'Code OTP requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = OneTimePassword.objects.get(code=otpcode, user__email=email)
            user = otp_obj.user

            is_valid, message = verify_otp(user, otpcode)

            if is_valid:
                user.is_active = True
                user.save()
                return Response({'message': 'Email vérifié avec succès.'}, status=status.HTTP_200_OK)

            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)

        except OneTimePassword.DoesNotExist:
            return Response({'message': 'Code invalide ou expiré.'}, status=status.HTTP_404_NOT_FOUND)


# 🔐 Login
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data  # ✅ C'est ici qu'on récupère les données validées
        user = data.get("user")
        return Response({
            "access": data["access_token"],
            "refresh": data["refresh_token"],
            "id": user.id,  # ou data.get("id") si tu veux vraiment inclure l'id ici
            "email": data["email"],
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username

        }, status=status.HTTP_200_OK)


# 🚪 Logout
class LogoutView(GenericAPIView):
    serializer_class=LogoutSerializer
    permission_classes=[IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Déconnexion réussie ✅'},status=status.HTTP_204_NO_CONTENT)



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


# 👤 Consulter & modifier son profil
class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 🔑 Réinitialisation du mot de passe (demande OTP)
class RequestResetPasswordAPIView(GenericAPIView):
    serializer_class = RequestResetPasswordAPISerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(
            {'message': "Un lien vous a été envoyé à votre boîte email pour réinitialiser votre mot de passe."},
            status=status.HTTP_200_OK
        )


# 🔒 Réinitialisation du mot de passe (confirmer)
class ConfirmResetPasswordWithOTPAPIView(GenericAPIView):
    def post(self, request):
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

        except DjangoUnicodeDecodeError:
            return Response({'message': 'Le token est invalide ou expiré'}, status=status.HTTP_401_UNAUTHORIZED)


# 3. Réinitialisation depuis lien web (POST avec n
# ouveau mot de passe)
class SetNewPassword(GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    permission_classes = [AllowAny]

    def patch(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Mot de passe modifié avec succès 👍'}, status=status.HTTP_200_OK)

class TestAuthenticationView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data={
            'msg':'ça fonctionne!'
        }
        return Response(data, status=status.HTTP_200_OK)
    
class GoogleSignInView(GenericAPIView):

    serializer_class = GoogleSignInSerializer
    authentication_classes = []  # si tu veux désactiver l’auth obligatoire
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Le validated_data contient déjà le dict avec access_token, refresh_token, etc.
        data = serializer.validated_data

        return Response(data, status=status.HTTP_200_OK)
    
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