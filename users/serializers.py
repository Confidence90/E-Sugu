# users/serializers.py
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from .models import User, VendorProfile, Address
import logging
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, smart_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import *
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import time


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(max_length=128, min_length=8, write_only=True)
    
    class Meta:
        model = User
        fields = ['id','first_name','last_name', 'username', 'email', 'country_code', 'phone', 
                 'password', 'password2', 'location', 'is_seller', 'role', 'is_active', 'is_staff', 'is_superuser']  # AJOUTER 'role'
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
            'phone': {'required': True, 'allow_blank': False},
            'id': {'read_only': True},
            'role': {'read_only': False},  # PERMETTRE L'ÉCRITURE
            'is_active': {'read_only': False},
            'is_staff': {'read_only': False},
            'is_superuser': {'read_only': False},
        }

    def validate_email(self, value):
        if value:
            if '@' not in value or not value:
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
    location_display = serializers.CharField(source='get_location_display', read_only=True)
    class Meta:
        model = User
        fields = ['id','full_name', 'first_name', 'last_name', 'email', 'country_code', 'phone', 'location','location_display', 'is_seller', 'created_at','avatar']
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

        

logger = logging.getLogger(__name__)

class RequestResetPasswordAPISerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    
    def validate_identifier(self, value):
        logger.info(f"🔍 Validation de l'identifiant: {value}")
        
        if '@' in value:
            try:
                user = User.objects.get(email=value)
                logger.info(f"✅ Utilisateur trouvé par email: {user.email} (ID: {user.id})")
                return value
            except User.DoesNotExist:
                logger.warning(f"❌ Aucun utilisateur avec l'email: {value}")
                raise serializers.ValidationError("Aucun utilisateur trouvé avec cet email.")
        
        elif value.startswith('+'):
            try:
                user = User.objects.get(phone_full=value)
                logger.info(f"✅ Utilisateur trouvé par téléphone: {user.phone_full}")
                return value
            except User.DoesNotExist:
                logger.warning(f"❌ Aucun utilisateur avec le téléphone: {value}")
                raise serializers.ValidationError("Aucun utilisateur trouvé avec ce numéro de téléphone.")
        
        else:
            raise serializers.ValidationError("Veuillez entrer un email valide ou un numéro de téléphone international (ex: +223...).")
    
    def save(self):
        identifier = self.validated_data['identifier']
        
        # Récupérer l'utilisateur
        if '@' in identifier:
            user = User.objects.get(email=identifier)
        else:
            user = User.objects.get(phone_full=identifier)
        
        # Générer le token
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.id))
        
        # ✅ SOLUTION 3 : Détection automatique
        if user.is_seller:
            # Frontend vendeur (port 5173)
            reset_url = f"http://localhost:5173/reset-password?uidb64={uidb64}&token={token}"
        else:
            # Frontend acheteur (port 5174) - CELUI QUE VOUS AVEZ
            reset_url = f"http://localhost:5173/reset-password?uidb64={uidb64}&token={token}"
        
        logger.info(f"🔗 Lien généré pour {user.email} (seller: {user.is_seller}): {reset_url}")
        
        try:
            send_password_reset_email(user, reset_url)
            logger.info(f"✅ Email de réinitialisation envoyé à {user.email}")
        except Exception as e:
            logger.error(f"❌ Erreur envoi email à {user.email}: {e}")
            raise serializers.ValidationError("Erreur lors de l'envoi de l'email.")
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

# serializers.py - Ajoutez cette classe
# Dans serializers.py - Ajoutez cette classe

class VendorProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    user_country_code = serializers.CharField(source='user.country_code', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = [
            'id', 
            'user_email', 'user_phone', 'user_country_code', 'user_first_name', 'user_last_name',
            # Informations boutique
            'shop_name', 'contact_name', 'contact_email', 'contact_phone',
            'customer_service_name', 'customer_service_phone', 'customer_service_email',
            'address_line1', 'address_line2', 'city', 'region',
            # Informations société
            'account_type', 'company_name', 'legal_representative', 'id_type',
            'tax_id', 'vat_number', 'legal_address',
            # Informations expédition
            'shipping_zone', 'use_business_address',
            'shipping_address_line1', 'shipping_address_line2', 'shipping_city',
            'shipping_state', 'shipping_zip',
            'return_address_line1', 'return_address_line2', 'return_city',
            'return_state', 'return_zip',
            # Informations complémentaires
            'has_existing_shop', 'vendor_type',
            # Métadonnées
            'is_completed', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'is_completed': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }

    def validate(self, attrs):
        # Validation pour les comptes entreprise
        if attrs.get('account_type') == 'company':
            if not attrs.get('company_name'):
                raise serializers.ValidationError({
                    "company_name": "Le nom de l'entreprise est requis pour les comptes professionnels."
                })
            if not attrs.get('legal_representative'):
                raise serializers.ValidationError({
                    "legal_representative": "Le représentant légal est requis pour les comptes professionnels."
                })
        
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        # Vérifier si un profil existe déjà
        if hasattr(user, 'vendor_profile'):
            raise serializers.ValidationError("Un profil vendeur existe déjà pour cet utilisateur.")
        
        validated_data['user'] = user
        return super().create(validated_data)
class AddressSerializer(serializers.ModelSerializer):
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = Address
        fields = [
            'id',
            'address_type',
            'first_name',
            'last_name',
            'phone',
            'additional_phone',
            'address_line1',
            'address_line2',
            'city',
            'region',
            'delivery_point',
            'tax_id',
            'additional_info',
            'is_default',
            'full_address',
            'created_at',
            'updated_at'
        ]
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def validate(self, attrs):
        # Validation pour s'assurer qu'au moins un numéro de téléphone est fourni
        if not attrs.get('phone'):
            raise serializers.ValidationError({"phone": "Le numéro de téléphone principal est requis."})
        
        # Validation pour s'assurer que l'adresse principale est fournie
        if not attrs.get('address_line1'):
            raise serializers.ValidationError({"address_line1": "L'adresse principale est requise."})
        
        # Validation pour s'assurer que la ville est fournie
        if not attrs.get('city'):
            raise serializers.ValidationError({"city": "La ville est requise."})
        
        return attrs

    def create(self, validated_data):
        # Ajouter l'utilisateur actuel aux données validées
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    

# users/serializers.py - AJOUTEZ CE SERIALIZER
class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer pour l'administration des utilisateurs"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    last_login_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name',
            'first_name', 'last_name',
            'phone', 'phone_full', 'country_code', 'location',
            'role', 'role_display',
            'is_seller', 'is_seller_pending',
            'is_active', 'is_verified',
            'is_staff', 'is_superuser',
            'auth_provider',
            'created_at', 'last_login', 'last_login_formatted',
            'vendor_profile'
        ]
        read_only_fields = ['created_at', 'last_login', 'phone_full']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() if obj.first_name or obj.last_name else obj.username
    
    def get_last_login_formatted(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%d/%m/%Y %H:%M')
        return 'Jamais connecté'