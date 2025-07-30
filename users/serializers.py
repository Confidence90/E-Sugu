# users/serializers.py
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from .models import User


from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, smart_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import send_normal_email
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import time


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(max_length=128, min_length=8, write_only=True)
    
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'username', 'email', 'country_code', 'phone', 'password', 'password2', 'location', 'is_seller']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
            'phone': {'required': True, 'allow_blank': False},
            'id': {'read_only': True},
        }

    def validate_email(self, value):
        if value:
            if '@' not in value or not value.endswith('.com'):
                raise serializers.ValidationError("L'email doit contenir '@' et se terminer par '.com'.")
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_phone(self, value):
        if not value.isdigit() or len(value) < 8:
            raise serializers.ValidationError("Le numéro de téléphone doit contenir au moins 8 chiffres.")
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return value

    def validate(self, attrs):
        password = attrs.get('password', '')
        password2 = attrs.get('password2', '')
        if 'username' not in attrs:
            attrs['username'] = attrs.get('email')
        
        if password != password2:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        
        # Validation de l'unicité du phone_full sans l'exposer dans les champs
        phone_full = f"{attrs['country_code']}{attrs['phone']}"
        if User.objects.filter(phone_full=phone_full).exists():
            raise serializers.ValidationError({"phone": "Ce numéro est déjà utilisé avec cet indicatif."})
            
        return attrs

    def create(self, validated_data):
        try:
            # Suppression du champ password2
            validated_data.pop('password2')
            
            # Extraction et hashage du mot de passe
            password = validated_data.pop('password')
            validated_data['is_verified'] = False
            validated_data['is_seller_pending'] = False
            # Création du phone_full avant la création de l'utilisateur
            validated_data['phone_full'] = f"{validated_data['country_code']}{validated_data['phone']}"
            
            # Création de l'utilisateur
            user = User(**validated_data)
            user.set_password(password)
            user.save()
            
            return user
        except Exception as e:
            raise serializers.ValidationError(f"Erreur lors de la création de l'utilisateur : {str(e)}")

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)
    full_name = serializers.CharField(max_length=255, read_only=True)
    access_token = serializers.CharField(max_length=255, read_only=True)
    refresh_token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, attrs):
        # Normalisation de l'email
        try:
            email = attrs['email'].lower().strip()
            validate_email(email)
        except (KeyError, ValidationError):
            time.sleep(2)  # Délai pour les emails invalides
            raise serializers.ValidationError("Email invalide")
            
        password = attrs.get('password')
        request = self.context.get('request')

        # Authentification
        user = authenticate(request, email=email, password=password)
        
        if not user:
            time.sleep(2)  # Délai pour les échecs d'authentification
            raise serializers.ValidationError("Email ou mot de passe incorrect.")
            
        if not user.is_active:
            raise serializers.ValidationError("Le compte est désactivé.")

        # Génération des tokens
        refresh = RefreshToken.for_user(user)
        
        # Ajout de claims personnalisés si nécessaire
        refresh['email'] = user.email
        refresh['full_name'] = f"{user.first_name} {user.last_name}".strip() or user.username

        return {
            "user": user,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id','full_name', 'first_name', 'last_name', 'email', 'country_code', 'phone', 'location', 'is_seller', 'created_at','avatar']
        extra_kwargs = {
            'id': {'read_only': True},
            'email': {'read_only': True},
            'created_at': {'read_only': True},
        }
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
#Nouveau
class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    confirm_password = serializers.CharField(max_length=100, min_length=6, write_only=True)
    uidb64 = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    class Meta:
        fields = ["password", "confirm_password", "uidb64", "token"]

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password != confirm_password:
            raise AuthenticationFailed("Les mots de passe ne correspondent pas ❌")

        try:
            uidb64 = attrs.get('uidb64')
            token = attrs.get('token')

            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            if not default_token_generator.check_token(user, token):
                raise AuthenticationFailed("Le lien est invalide ou expiré 🙄")

            attrs['user'] = user  # ✅ on transmet l'utilisateur pour la méthode save()

        except User.DoesNotExist:
            raise AuthenticationFailed("Utilisateur introuvable.")

        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        password = self.validated_data['password']
        user.set_password(password)
        user.save()
        return user

        

class RequestResetPasswordAPISerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    def validate(self, attrs):
        email = attrs.get('email')

        # Vérification de l'existence de l'utilisateur
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Aucun utilisateur avec cet email.")

        user = User.objects.get(email=email)
        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = PasswordResetTokenGenerator().make_token(user)

        request = self.context.get('request')
        site_domain = get_current_site(request).domain
        relative_link = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
        abslink = f"http://{site_domain}{relative_link}"

        email_body = f"""
        Bonjour {user.first_name},

        Vous avez demandé une réinitialisation de votre mot de passe.

        Cliquez sur ce lien pour définir un nouveau mot de passe :
        {abslink}

        Si vous n'êtes pas à l'origine de cette demande, ignorez simplement ce message.

        Merci,
        L’équipe E-Sugu
        """
        data = {
            'email_body': email_body,
            'email_subject': "Réinitialisation de votre mot de passe",
            'to_email': user.email
        }

        send_normal_email(data)  # Tu dois définir cette fonction dans `utils.py`
        return attrs
    

class LogoutSerializer(serializers.Serializer):

    refresh_token = serializers.CharField()

    default_error_messages = {
        'bad_token': 'Jeton invalide ou expiré !'
    }

    def validate(self, attrs):
        self.token = attrs.get('refresh_token')
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            self.fail('bad_token')

