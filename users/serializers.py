# users/serializers.py
from rest_framework import serializers
from .models import User
import phonenumbers
from twilio.rest import Client
from django.conf import settings

class UserSerializer(serializers.ModelSerializer):
    country_code = serializers.CharField()
    phone = serializers.CharField(max_length=15)

    class Meta:
        model = User
        fields = ['name', 'email', 'country_code', 'phone', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        phone_number = f"{data['country_code']}{data['phone']}"
        try:
            parsed = phonenumbers.parse(phone_number)
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError("Numéro de téléphone invalide")
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Format de numéro incorrect")
        if User.objects.filter(phone_full=phone_number).exists():
            raise serializers.ValidationError("Ce numéro est déjà utilisé")
        data['phone_full'] = phone_number
        return data

    def create(self, validated_data):
        user = User(
            name=validated_data['name'],
            email=validated_data.get('email'),
            country_code=validated_data['country_code'],
            phone=validated_data['phone'],
            phone_full=validated_data['phone_full'],
            password=validated_data['password']
        )
        user.save()
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        verification = client.verify.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=user.phone_full, channel='sms'
        )
        return user

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'country_code', 'phone', 'location', 'stripe_account_id']
        read_only_fields = ['id', 'country_code', 'phone']