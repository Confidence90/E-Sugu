# users/serializers.py
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    phone_full = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'country_code', 'phone', 'phone_full', 'password', 'location', 'is_seller']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
        }

    def validate_email(self, value):
        if value and not '@' in value:
            raise serializers.ValidationError("L'email doit être valide.")
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_phone(self, value):
        if not value.isdigit() or len(value) < 8:
            raise serializers.ValidationError("Le numéro de téléphone doit contenir au moins 8 chiffres.")
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return value

    def validate(self, data):
        phone_full = f"{data['country_code']}{data['phone']}"
        if User.objects.filter(phone_full=phone_full).exists():
            raise serializers.ValidationError({"phone_full": "Ce numéro complet est déjà utilisé."})
        data['phone_full'] = phone_full
        return data

    def create(self, validated_data):
        try:
            user = User(
                name=validated_data['name'],
                email=validated_data.get('email'),
                country_code=validated_data['country_code'],
                phone=validated_data['phone'],
                phone_full=validated_data['phone_full'],
                password=validated_data['password'],
                location=validated_data.get('location'),
                is_seller=validated_data.get('is_seller', False),
                is_active=True
            )
            user.save()
            return user
        except Exception as e:
            raise serializers.ValidationError(f"Erreur lors de la création de l'utilisateur : {str(e)}")

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data['identifier']
        password = data['password']
        try:
            user = User.objects.get(phone_full=identifier) if identifier.startswith('+') else User.objects.get(email=identifier)
            if not user.check_password(password):
                raise serializers.ValidationError({"password": "Mot de passe incorrect."})
            if not user.is_active:
                raise serializers.ValidationError({"non_field_errors": "Compte non activé."})
            data['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError({"non_field_errors": "Utilisateur non trouvé."})
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'country_code', 'phone', 'location', 'is_seller', 'created_at']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
        }